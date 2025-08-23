# Auto-generate CLI from function signatures and docstrings - Help Formatter
import argparse
import inspect
import os
import textwrap
from typing import Any

from .docstring_parser import extract_function_help


class HierarchicalHelpFormatter(argparse.RawDescriptionHelpFormatter):
  """Custom formatter providing clean hierarchical command display."""

  def __init__(self, *args, theme=None, **kwargs):
    super().__init__(*args, **kwargs)
    try:
      self._console_width=os.get_terminal_size().columns
    except (OSError, ValueError):
      # Fallback for non-TTY environments (pipes, redirects, etc.)
      self._console_width=int(os.environ.get('COLUMNS', 80))
    self._cmd_indent=2  # Base indentation for commands
    self._arg_indent=6  # Indentation for arguments
    self._desc_indent=8  # Indentation for descriptions

    # Theme support
    self._theme=theme
    if theme:
      from .theme import ColorFormatter
      self._color_formatter=ColorFormatter()
    else:
      self._color_formatter=None

    # Cache for global column calculation
    self._global_desc_column=None

  def _format_actions(self, actions):
    """Override to capture parser actions for unified column calculation."""
    # Store actions for unified column calculation
    self._parser_actions = actions
    return super()._format_actions(actions)

  def _format_action(self, action):
    """Format actions with proper indentation for subcommands."""
    if isinstance(action, argparse._SubParsersAction):
      return self._format_subcommands(action)

    # Handle global options with fixed alignment
    if action.option_strings and not isinstance(action, argparse._SubParsersAction):
      return self._format_global_option_aligned(action)

    return super()._format_action(action)

  def _ensure_global_column_calculated(self):
    """Calculate and cache the unified description column if not already done."""
    if self._global_desc_column is not None:
      return self._global_desc_column

    # Find subparsers action from parser actions that were passed to the formatter
    subparsers_action = None
    parser_actions = getattr(self, '_parser_actions', [])

    # Find subparsers action from parser actions
    for act in parser_actions:
      if isinstance(act, argparse._SubParsersAction):
        subparsers_action = act
        break

    if subparsers_action:
      # Use the unified command description column for consistency - this already includes all options
      self._global_desc_column = self._calculate_unified_command_description_column(subparsers_action)
    else:
      # Fallback: Use a reasonable default
      self._global_desc_column = 40

    return self._global_desc_column

  def _format_global_option_aligned(self, action):
    """Format global options with consistent alignment using existing alignment logic."""
    # Build option string
    option_strings = action.option_strings
    if not option_strings:
      return super()._format_action(action)

    # Get option name (prefer long form)
    option_name = option_strings[-1] if option_strings else ""

    # Add metavar if present
    if action.nargs != 0:
      if hasattr(action, 'metavar') and action.metavar:
        option_display = f"{option_name} {action.metavar}"
      elif hasattr(action, 'choices') and action.choices:
        # For choices, show them in help text, not in option name
        option_display = option_name
      else:
        # Generate metavar from dest
        metavar = action.dest.upper().replace('_', '-')
        option_display = f"{option_name} {metavar}"
    else:
      option_display = option_name

    # Prepare help text
    help_text = action.help or ""
    if hasattr(action, 'choices') and action.choices and action.nargs != 0:
      # Add choices info to help text
      choices_str = ", ".join(str(c) for c in action.choices)
      help_text = f"{help_text} (choices: {choices_str})"

    # Get the cached global description column
    global_desc_column = self._ensure_global_column_calculated()

    # Use the existing _format_inline_description method for proper alignment and wrapping
    # Use the same indentation as command options for consistent alignment
    formatted_lines = self._format_inline_description(
      name=option_display,
      description=help_text,
      name_indent=self._arg_indent,  # Use same 6-space indent as command options
      description_column=global_desc_column,  # Use calculated global column for global options
      style_name='option_name',  # Use option_name style (will be handled by CLI theme)
      style_description='option_description',  # Use option_description style
      add_colon=False  # Options don't have colons
    )

    # Join lines and add newline at end
    return '\n'.join(formatted_lines) + '\n'

  def _calculate_global_option_column(self, action):
    """Calculate global option description column based on longest option across ALL commands."""
    max_opt_width=self._arg_indent

    # Scan all flat commands
    for choice, subparser in action.choices.items():
      if not hasattr(subparser, '_command_type') or subparser._command_type != 'group':
        _, optional_args=self._analyze_arguments(subparser)
        for arg_name, _ in optional_args:
          opt_width=len(arg_name) + self._arg_indent
          max_opt_width=max(max_opt_width, opt_width)

    # Scan all group subcommands
    for choice, subparser in action.choices.items():
      if hasattr(subparser, '_command_type') and subparser._command_type == 'group':
        if hasattr(subparser, '_subcommands'):
          for subcmd_name in subparser._subcommands.keys():
            subcmd_parser=self._find_subparser(subparser, subcmd_name)
            if subcmd_parser:
              _, optional_args=self._analyze_arguments(subcmd_parser)
              for arg_name, _ in optional_args:
                opt_width=len(arg_name) + self._arg_indent
                max_opt_width=max(max_opt_width, opt_width)

    # Calculate global description column with padding
    global_opt_desc_column=max_opt_width + 4  # 4 spaces padding

    # Ensure we don't exceed terminal width (leave room for descriptions)
    return min(global_opt_desc_column, self._console_width // 2)

  def _calculate_unified_command_description_column(self, action):
    """Calculate unified description column for ALL elements (global options, commands, subcommands, AND options)."""
    max_width=self._cmd_indent

    # Include global options in the calculation
    parser_actions = getattr(self, '_parser_actions', [])
    for act in parser_actions:
      if act.option_strings and act.dest != 'help' and not isinstance(act, argparse._SubParsersAction):
        opt_name = act.option_strings[-1]
        if act.nargs != 0 and getattr(act, 'metavar', None):
          opt_display = f"{opt_name} {act.metavar}"
        elif act.nargs != 0:
          opt_metavar = act.dest.upper().replace('_', '-')
          opt_display = f"{opt_name} {opt_metavar}"
        else:
          opt_display = opt_name
        # Global options use same 6-space indent as command options
        global_opt_width = len(opt_display) + self._arg_indent
        max_width = max(max_width, global_opt_width)

    # Scan all flat commands and their options
    for choice, subparser in action.choices.items():
      if not hasattr(subparser, '_command_type') or subparser._command_type != 'group':
        # Calculate command width: indent + name + colon
        cmd_width=self._cmd_indent + len(choice) + 1  # +1 for colon
        max_width=max(max_width, cmd_width)
        
        # Also check option widths in flat commands
        _, optional_args=self._analyze_arguments(subparser)
        for arg_name, _ in optional_args:
          opt_width=len(arg_name) + self._arg_indent
          max_width=max(max_width, opt_width)

    # Scan all group commands and their subcommands/options
    for choice, subparser in action.choices.items():
      if hasattr(subparser, '_command_type') and subparser._command_type == 'group':
        # Calculate group command width: indent + name + colon
        cmd_width=self._cmd_indent + len(choice) + 1  # +1 for colon
        max_width=max(max_width, cmd_width)
        
        # Also check subcommands within groups
        if hasattr(subparser, '_subcommands'):
          subcommand_indent=self._cmd_indent + 2
          for subcmd_name in subparser._subcommands.keys():
            # Calculate subcommand width: subcommand_indent + name + colon
            subcmd_width=subcommand_indent + len(subcmd_name) + 1  # +1 for colon
            max_width=max(max_width, subcmd_width)
            
            # Also check option widths in subcommands
            subcmd_parser=self._find_subparser(subparser, subcmd_name)
            if subcmd_parser:
              _, optional_args=self._analyze_arguments(subcmd_parser)
              for arg_name, _ in optional_args:
                opt_width=len(arg_name) + self._arg_indent
                max_width=max(max_width, opt_width)

    # Add padding for description (4 spaces minimum)
    unified_desc_column=max_width + 4

    # Ensure we don't exceed terminal width (leave room for descriptions)
    return min(unified_desc_column, self._console_width // 2)

  def _format_subcommands(self, action):
    """Format subcommands with clean list-based display."""
    parts=[]
    groups={}
    flat_commands={}
    has_required_args=False

    # Calculate unified command description column for consistent alignment across ALL command types
    unified_cmd_desc_column=self._calculate_unified_command_description_column(action)
    
    # Calculate global option column for consistent alignment across all commands
    global_option_column=self._calculate_global_option_column(action)

    # Separate groups from flat commands
    for choice, subparser in action.choices.items():
      if hasattr(subparser, '_command_type'):
        if subparser._command_type == 'group':
          groups[choice]=subparser
        else:
          flat_commands[choice]=subparser
      else:
        flat_commands[choice]=subparser

    # Add flat commands with unified command description column alignment
    for choice, subparser in sorted(flat_commands.items()):
      command_section=self._format_command_with_args_global(choice, subparser, self._cmd_indent, unified_cmd_desc_column, global_option_column)
      parts.extend(command_section)
      # Check if this command has required args
      required_args, _=self._analyze_arguments(subparser)
      if required_args:
        has_required_args=True

    # Add groups with their subcommands
    if groups:
      if flat_commands:
        parts.append("")  # Empty line separator

      for choice, subparser in sorted(groups.items()):
        group_section=self._format_group_with_subcommands_global(
          choice, subparser, self._cmd_indent, unified_cmd_desc_column, global_option_column
          )
        parts.extend(group_section)
        # Check subcommands for required args too
        if hasattr(subparser, '_subcommand_details'):
          for subcmd_info in subparser._subcommand_details.values():
            if subcmd_info.get('type') == 'command' and 'function' in subcmd_info:
              # This is a bit tricky - we'd need to check the function signature
              # For now, assume nested commands might have required args
              has_required_args=True

    # Add footnote if there are required arguments
    if has_required_args:
      parts.append("")  # Empty line before footnote
      # Style the entire footnote to match the required argument asterisks
      if hasattr(self, '_theme') and self._theme:
        from .theme import ColorFormatter
        color_formatter=ColorFormatter()
        styled_footnote=color_formatter.apply_style("* - required", self._theme.required_asterisk)
        parts.append(styled_footnote)
      else:
        parts.append("* - required")

    return "\n".join(parts)

  def _format_command_with_args_global(self, name, parser, base_indent, unified_cmd_desc_column, global_option_column):
    """Format a command with unified command description column alignment."""
    lines=[]

    # Get required and optional arguments
    required_args, optional_args=self._analyze_arguments(parser)

    # Command line (keep name only, move required args to separate lines)
    command_name=name

    # These are flat commands when using this method
    name_style='command_name'
    desc_style='command_description'

    # Format description for flat command (with colon and unified column alignment)
    help_text=parser.description or getattr(parser, 'help', '')
    styled_name=self._apply_style(command_name, name_style)

    if help_text:
      # Use unified command description column for consistent alignment
      formatted_lines = self._format_inline_description(
        name=command_name,
        description=help_text,
        name_indent=base_indent,
        description_column=unified_cmd_desc_column,  # Use unified column for consistency
        style_name=name_style,
        style_description=desc_style,
        add_colon=True
      )
      lines.extend(formatted_lines)
    else:
      # Just the command name with styling
      lines.append(f"{' ' * base_indent}{styled_name}")

    # Add required arguments as a list (now on separate lines)
    if required_args:
      for arg_name in required_args:
        styled_req=self._apply_style(arg_name, 'required_option_name')
        styled_asterisk=self._apply_style(" *", 'required_asterisk')
        lines.append(f"{' ' * self._arg_indent}{styled_req}{styled_asterisk}")

    # Add optional arguments with unified command description column alignment
    if optional_args:
      for arg_name, arg_help in optional_args:
        styled_opt=self._apply_style(arg_name, 'option_name')
        if arg_help:
          # Use unified command description column for ALL descriptions (commands and options)
          opt_lines=self._format_inline_description(
            name=arg_name,
            description=arg_help,
            name_indent=self._arg_indent,
            description_column=unified_cmd_desc_column,  # Use same column as command descriptions
            style_name='option_name',
            style_description='option_description'
          )
          lines.extend(opt_lines)
        else:
          # Just the option name with styling
          lines.append(f"{' ' * self._arg_indent}{styled_opt}")

    return lines

  def _format_group_with_subcommands_global(self, name, parser, base_indent, unified_cmd_desc_column, global_option_column):
    """Format a command group with unified command description column alignment."""
    lines=[]
    indent_str=" " * base_indent

    # Group header with special styling for group commands
    styled_group_name=self._apply_style(name, 'group_command_name')

    # Check for CommandGroup description
    group_description = getattr(parser, '_command_group_description', None)
    if group_description:
      # Use unified command description column for consistent formatting
      formatted_lines = self._format_inline_description(
        name=name,
        description=group_description,
        name_indent=base_indent,
        description_column=unified_cmd_desc_column,  # Use unified column for consistency
        style_name='group_command_name',
        style_description='command_description',  # Reuse command description style
        add_colon=True
      )
      lines.extend(formatted_lines)
    else:
      # Default group display
      lines.append(f"{indent_str}{styled_group_name}")

      # Group description
      help_text=parser.description or getattr(parser, 'help', '')
      if help_text:
        wrapped_desc=self._wrap_text(help_text, self._desc_indent, self._console_width)
        lines.extend(wrapped_desc)

    # Find and format subcommands with unified command description column alignment
    if hasattr(parser, '_subcommands'):
      subcommand_indent=base_indent + 2

      for subcmd, subcmd_help in sorted(parser._subcommands.items()):
        # Find the actual subparser
        subcmd_parser=self._find_subparser(parser, subcmd)
        if subcmd_parser:
          subcmd_section=self._format_command_with_args_global_subcommand(
            subcmd, subcmd_parser, subcommand_indent,
            unified_cmd_desc_column, global_option_column
          )
          lines.extend(subcmd_section)
        else:
          # Fallback for cases where we can't find the parser
          lines.append(f"{' ' * subcommand_indent}{subcmd}")
          if subcmd_help:
            wrapped_help=self._wrap_text(subcmd_help, subcommand_indent + 2, self._console_width)
            lines.extend(wrapped_help)

    return lines

  def _calculate_group_dynamic_columns(self, group_parser, cmd_indent, opt_indent):
    """Calculate dynamic columns for an entire group of subcommands."""
    max_cmd_width=0
    max_opt_width=0

    # Analyze all subcommands in the group
    if hasattr(group_parser, '_subcommands'):
      for subcmd_name in group_parser._subcommands.keys():
        subcmd_parser=self._find_subparser(group_parser, subcmd_name)
        if subcmd_parser:
          # Check command name width
          cmd_width=len(subcmd_name) + cmd_indent
          max_cmd_width=max(max_cmd_width, cmd_width)

          # Check option widths
          _, optional_args=self._analyze_arguments(subcmd_parser)
          for arg_name, _ in optional_args:
            opt_width=len(arg_name) + opt_indent
            max_opt_width=max(max_opt_width, opt_width)

    # Calculate description columns with padding
    cmd_desc_column=max_cmd_width + 4  # 4 spaces padding
    opt_desc_column=max_opt_width + 4  # 4 spaces padding

    # Ensure we don't exceed terminal width (leave room for descriptions)
    max_cmd_desc=min(cmd_desc_column, self._console_width // 2)
    max_opt_desc=min(opt_desc_column, self._console_width // 2)

    # Ensure option descriptions are at least 2 spaces more indented than command descriptions
    if max_opt_desc <= max_cmd_desc + 2:
      max_opt_desc=max_cmd_desc + 2

    return max_cmd_desc, max_opt_desc

  def _format_command_with_args_global_subcommand(self, name, parser, base_indent, unified_cmd_desc_column, global_option_column):
    """Format a subcommand with unified command description column alignment."""
    lines=[]

    # Get required and optional arguments
    required_args, optional_args=self._analyze_arguments(parser)

    # Command line (keep name only, move required args to separate lines)
    command_name=name

    # These are always subcommands when using this method
    name_style='subcommand_name'
    desc_style='subcommand_description'

    # Format description with unified command description column for consistency
    help_text=parser.description or getattr(parser, 'help', '')
    styled_name=self._apply_style(command_name, name_style)

    if help_text:
      # Use unified command description column for consistent alignment with all commands
      formatted_lines=self._format_inline_description(
        name=command_name,
        description=help_text,
        name_indent=base_indent,
        description_column=unified_cmd_desc_column,  # Unified column for consistency across all command types
        style_name=name_style,
        style_description=desc_style,
        add_colon=True  # Add colon for subcommands
      )
      lines.extend(formatted_lines)
    else:
      # Just the command name with styling
      lines.append(f"{' ' * base_indent}{styled_name}")

    # Add required arguments as a list (now on separate lines)
    if required_args:
      for arg_name in required_args:
        styled_req=self._apply_style(arg_name, 'required_option_name')
        styled_asterisk=self._apply_style(" *", 'required_asterisk')
        lines.append(f"{' ' * self._arg_indent}{styled_req}{styled_asterisk}")

    # Add optional arguments with unified command description column alignment
    if optional_args:
      for arg_name, arg_help in optional_args:
        styled_opt=self._apply_style(arg_name, 'option_name')
        if arg_help:
          # Use unified command description column for ALL descriptions (commands and options)
          opt_lines=self._format_inline_description(
            name=arg_name,
            description=arg_help,
            name_indent=self._arg_indent,
            description_column=unified_cmd_desc_column,  # Use same column as command descriptions
            style_name='option_name',
            style_description='option_description'
          )
          lines.extend(opt_lines)
        else:
          # Just the option name with styling
          lines.append(f"{' ' * self._arg_indent}{styled_opt}")

    return lines

  def _analyze_arguments(self, parser):
    """Analyze parser arguments and return required and optional separately."""
    if not parser:
      return [], []

    required_args=[]
    optional_args=[]

    for action in parser._actions:
      if action.dest == 'help':
        continue

      arg_name=f"--{action.dest.replace('_', '-')}"
      arg_help=getattr(action, 'help', '')

      if hasattr(action, 'required') and action.required:
        # Required argument - we'll add styled asterisk later in formatting
        if hasattr(action, 'metavar') and action.metavar:
          required_args.append(f"{arg_name} {action.metavar}")
        else:
          required_args.append(f"{arg_name} {action.dest.upper()}")
      elif action.option_strings:
        # Optional argument - add to list display
        if action.nargs == 0 or getattr(action, 'action', None) == 'store_true':
          # Boolean flag
          optional_args.append((arg_name, arg_help))
        else:
          # Value argument
          if hasattr(action, 'metavar') and action.metavar:
            arg_display=f"{arg_name} {action.metavar}"
          else:
            arg_display=f"{arg_name} {action.dest.upper()}"
          optional_args.append((arg_display, arg_help))

    return required_args, optional_args

  def _wrap_text(self, text, indent, width):
    """Wrap text with proper indentation using textwrap."""
    if not text:
      return []

    # Calculate available width for text
    available_width=max(width - indent, 20)  # Minimum 20 chars

    # Use textwrap to handle the wrapping
    wrapper=textwrap.TextWrapper(
      width=available_width,
      initial_indent=" " * indent,
      subsequent_indent=" " * indent,
      break_long_words=False,
      break_on_hyphens=False
    )

    return wrapper.wrap(text)

  def _apply_style(self, text: str, style_name: str) -> str:
    """Apply theme style to text if theme is available."""
    if not self._theme or not self._color_formatter:
      return text

    # Map style names to theme attributes
    style_map={
      'title':self._theme.title,
      'subtitle':self._theme.subtitle,
      'command_name':self._theme.command_name,
      'command_description':self._theme.command_description,
      'group_command_name':self._theme.group_command_name,
      'subcommand_name':self._theme.subcommand_name,
      'subcommand_description':self._theme.subcommand_description,
      'option_name':self._theme.option_name,
      'option_description':self._theme.option_description,
      'required_option_name':self._theme.required_option_name,
      'required_option_description':self._theme.required_option_description,
      'required_asterisk':self._theme.required_asterisk
    }

    style=style_map.get(style_name)
    if style:
      return self._color_formatter.apply_style(text, style)
    return text

  def _get_display_width(self, text: str) -> int:
    """Get display width of text, handling ANSI color codes."""
    if not text:
      return 0

    # Strip ANSI escape sequences for width calculation
    import re
    ansi_escape=re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_text=ansi_escape.sub('', text)
    return len(clean_text)

  def _format_inline_description(
      self,
      name: str,
      description: str,
      name_indent: int,
      description_column: int,
      style_name: str,
      style_description: str,
      add_colon: bool = False
  ) -> list[str]:
    """Format name and description inline with consistent wrapping.

    :param name: The command/option name to display
    :param description: The description text
    :param name_indent: Indentation for the name
    :param description_column: Column where description should start
    :param style_name: Theme style for the name
    :param style_description: Theme style for the description
    :return: List of formatted lines
    """
    if not description:
      # No description, just return the styled name (with colon if requested)
      styled_name=self._apply_style(name, style_name)
      display_name=f"{styled_name}:" if add_colon else styled_name
      return [f"{' ' * name_indent}{display_name}"]

    styled_name=self._apply_style(name, style_name)
    styled_description=self._apply_style(description, style_description)

    # Create the full line with proper spacing (add colon if requested)
    display_name=f"{styled_name}:" if add_colon else styled_name
    name_part=f"{' ' * name_indent}{display_name}"
    name_display_width=name_indent + self._get_display_width(name) + (1 if add_colon else 0)

    # Calculate spacing needed to reach description column
    if add_colon:
      # For commands/subcommands with colons, use exactly 1 space after colon
      spacing_needed=1
      spacing=name_display_width + spacing_needed
    else:
      # For options, use column alignment
      spacing_needed=description_column - name_display_width
      spacing=description_column

      if name_display_width >= description_column:
        # Name is too long, use minimum spacing (4 spaces)
        spacing_needed=4
        spacing=name_display_width + spacing_needed

    # Try to fit everything on first line
    first_line=f"{name_part}{' ' * spacing_needed}{styled_description}"

    # Check if first line fits within console width
    if self._get_display_width(first_line) <= self._console_width:
      # Everything fits on one line
      return [first_line]

    # Need to wrap - start with name and first part of description on same line
    available_width_first_line=self._console_width - name_display_width - spacing_needed

    if available_width_first_line >= 20:  # Minimum readable width for first line
      # For wrapping, we need to work with the unstyled description text to get proper line breaks
      # then apply styling to each wrapped line
      wrapper=textwrap.TextWrapper(
        width=available_width_first_line,
        break_long_words=False,
        break_on_hyphens=False
      )
      desc_lines=wrapper.wrap(description)  # Use unstyled description for accurate wrapping

      if desc_lines:
        # First line with name and first part of description (apply styling to first line)
        styled_first_desc=self._apply_style(desc_lines[0], style_description)
        lines=[f"{name_part}{' ' * spacing_needed}{styled_first_desc}"]

        # Continuation lines with remaining description
        if len(desc_lines) > 1:
          # Calculate where the description text actually starts on the first line
          desc_start_position=name_display_width + spacing_needed
          continuation_indent=" " * desc_start_position
          for desc_line in desc_lines[1:]:
            styled_desc_line=self._apply_style(desc_line, style_description)
            lines.append(f"{continuation_indent}{styled_desc_line}")

        return lines

    # Fallback: put description on separate lines (name too long or not enough space)
    lines=[name_part]

    if add_colon:
      # For flat commands with colons, align with where description would start (name + colon + 1 space)
      desc_indent=name_display_width + spacing_needed
    else:
      # For options, use the original spacing calculation
      desc_indent=spacing

    available_width=self._console_width - desc_indent
    if available_width < 20:  # Minimum readable width
      available_width=20
      desc_indent=self._console_width - available_width

    # Wrap the description text (use unstyled text for accurate wrapping)
    wrapper=textwrap.TextWrapper(
      width=available_width,
      break_long_words=False,
      break_on_hyphens=False
    )

    desc_lines=wrapper.wrap(description)  # Use unstyled description for accurate wrapping
    indent_str=" " * desc_indent

    for desc_line in desc_lines:
      styled_desc_line=self._apply_style(desc_line, style_description)
      lines.append(f"{indent_str}{styled_desc_line}")

    return lines

  def _format_usage(self, usage, actions, groups, prefix):
    """Override to add color to usage line and potentially title."""
    usage_text=super()._format_usage(usage, actions, groups, prefix)

    # If this is the main parser (not a subparser), prepend styled title
    if prefix == 'usage: ' and hasattr(self, '_root_section'):
      # Try to get the parser description (title)
      parser=getattr(self._root_section, 'formatter', None)
      if parser:
        parser_obj=getattr(parser, '_parser', None)
        if parser_obj and hasattr(parser_obj, 'description') and parser_obj.description:
          styled_title=self._apply_style(parser_obj.description, 'title')
          return f"{styled_title}\n\n{usage_text}"

    return usage_text

  def _find_subparser(self, parent_parser, subcmd_name):
    """Find a subparser by name in the parent parser."""
    for action in parent_parser._actions:
      if isinstance(action, argparse._SubParsersAction):
        if subcmd_name in action.choices:
          return action.choices[subcmd_name]
    return None
