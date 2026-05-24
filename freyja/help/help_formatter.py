"""Hierarchical help formatter — renders themed help text for argparse parsers.

Layout rules (see ``~/.claude/plans/update-usage-formatting-so-flickering-toast.md``):

* Console width is detected from ``$COLUMNS`` → ``os.get_terminal_size()`` → 100 fallback,
  clamped to [40, 200].
* The description column ``desc_start_col`` is computed once from the longest visible
  name across all rows, rounded up to the next even number in ``[name_max + 3, name_max + 4]``
  with a 32-character floor, capped at half the console width.
* Per-row indents (depth 0): command groups 2, sub-commands 4, command-group options 6,
  sub-command options 8. Deeper nesting recurses with +2 increments.
* Description column for any row = ``desc_start_col + row_indent``.
* Wrapped description continuations hang-indent at ``desc_col + 4``.
* Options are alphabetized under their owning command (required + optional interleaved);
  the trailing ``*`` is a badge, not a sort key.
* Sub-command rows (no leading dash) and command-option rows (always leading ``--``) can
  share an indent column at deeper nesting; the dash-prefix invariant disambiguates them.
"""

from __future__ import annotations

import argparse
import os
import re
import textwrap
from collections.abc import Iterable
from typing import Any

from freyja.theme import ColorFormatter, get_no_color_theme

# Indent constants for depth-0 rendering (referenced by tests).
INDENT_COMMAND = 2
INDENT_SUBCOMMAND = 4
INDENT_COMMAND_OPTION = 6
INDENT_SUBCOMMAND_OPTION = 8
DESC_START_COL_MIN = 32

_ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def _strip_ansi(text: str) -> str:
  """Return ``text`` with ANSI escape sequences removed."""
  return _ANSI_ESCAPE.sub('', text or '')


def _display_width(text: str) -> int:
  """Return the visible width of ``text`` (ANSI escapes stripped)."""
  return len(_strip_ansi(text))


def detect_console_width() -> int:
  """Detect the current terminal width, clamped to ``[40, 200]``.

  Order of precedence: ``$COLUMNS`` env var, ``os.get_terminal_size().columns``, then 100.
  """
  raw: int | None = None
  env_val = os.environ.get('COLUMNS')
  if env_val:
    try:
      raw = int(env_val)
    except ValueError:
      raw = None
  if raw is None:
    try:
      raw = os.get_terminal_size().columns
    except (OSError, ValueError):
      raw = 100
  return max(40, min(200, raw))


def compute_desc_start_col(name_max: int, console_width: int) -> int:
  """Compute the description start column for the longest visible name.

  Rule: ``max(32, name_max + (4 if name_max is even else 3))``, capped at
  ``console_width // 2``. The +3/+4 selection guarantees the resulting column is even.
  """
  candidate = name_max + (4 if name_max % 2 == 0 else 3)
  floored = max(DESC_START_COL_MIN, candidate)
  return min(floored, console_width // 2)


class HierarchicalHelpFormatter(argparse.HelpFormatter):
  """Argparse formatter rendering Freyja's hierarchical help layout."""

  def __init__(self, *args: Any, theme: Any = None, alphabetize: bool = True, **kwargs: Any):
    """Initialize the formatter with optional theme + alphabetization settings."""
    super().__init__(*args, **kwargs)
    self._console_width = detect_console_width()
    # Argparse 3.14+ writes a private _theme attribute after __init__; we use a different
    # name to avoid clobbering.
    self._freyja_theme = theme if theme is not None else get_no_color_theme()
    self._color_formatter = ColorFormatter()
    self._alphabetize = alphabetize
    self._desc_start_col: int | None = None
    self._parser_actions: list[argparse.Action] = []

  # ----- argparse integration ----------------------------------------------------------

  def add_usage(
    self,
    usage: str | None,
    actions: Iterable[argparse.Action],
    groups: Iterable[argparse._MutuallyExclusiveGroup],
    prefix: str | None = None,
  ) -> None:
    """Capture the parser's full action list before sections are rendered."""
    action_list = list(actions)
    self._parser_actions = action_list
    super().add_usage(usage, action_list, groups, prefix)

  def _format_action(self, action: argparse.Action) -> str:
    """Render an action — command tree, themed option/positional, or default fallback."""
    if isinstance(action, argparse._SubParsersAction):
      output = self._format_subparsers_action(action) + '\n'
    elif action.dest == 'help':
      output = self._format_option_action(action) + '\n'
    elif action.option_strings or not isinstance(action, argparse._SubParsersAction):
      output = self._format_option_action(action) + '\n'
    else:
      output = super()._format_action(action)
    return output

  def start_section(self, heading: str | None) -> None:
    """Override section headings so they get the subtitle style consistently."""
    styled = heading
    if heading:
      upper = heading.upper()
      styled = self._apply_style(upper, 'subtitle')
    super().start_section(styled)

  # ----- desc_start_col calculation ----------------------------------------------------

  def _ensure_desc_start_col(self) -> int:
    """Compute (once) and cache the description column for this formatter."""
    if self._desc_start_col is None:
      name_widths = list(self._collect_name_widths())
      name_max = max(name_widths) if name_widths else 0
      self._desc_start_col = compute_desc_start_col(name_max, self._console_width)
    return self._desc_start_col

  def _collect_name_widths(self) -> list[int]:
    """Yield the visible widths of every name that will appear in this help block.

    Walks all parser actions: option strings (with metavar), the top-level subparsers
    action, and recursively every nested subparser tree. The trailing colon (groups +
    sub-commands) and the ``" *"`` required badge are included.
    """
    widths: list[int] = []
    for action in self._parser_actions:
      if isinstance(action, argparse._SubParsersAction):
        widths.extend(self._collect_subparser_widths(action))
      elif action.dest != 'help':
        name, _, required = self._extract_arg(action)
        widths.append(len(name) + (2 if required else 0))
    return widths

  def _collect_subparser_widths(self, action: argparse._SubParsersAction) -> list[int]:
    """Walk a subparsers tree and yield all command/option widths within it."""
    widths: list[int] = []
    for choice_name, sub_parser in action.choices.items():
      widths.append(len(choice_name) + 1)  # +1 for trailing ":"
      for opt_name, _help, required in self._extract_options(sub_parser):
        widths.append(len(opt_name) + (2 if required else 0))
      nested = self._find_subparsers_action(sub_parser)
      if nested is not None:
        widths.extend(self._collect_subparser_widths(nested))
    return widths

  def _desc_col_for_indent(self, indent: int) -> int:
    """Return the description column for a row at the given indent."""
    return self._ensure_desc_start_col() + indent

  # ----- option / action introspection -------------------------------------------------

  def _extract_arg(self, action: argparse.Action) -> tuple[str, str, bool]:
    """Return ``(display_name, help_text, is_required)`` for an action.

    Both option (``--foo``) and positional actions are rendered as ``--name VALUE``
    in the help body so visual structure stays consistent. Positionals are reported
    as required when they have no default.
    """
    clean_name = action.dest
    if clean_name.startswith('_subglobal_'):
      # Sub-global dest format: "_subglobal_<group>_<param>". Group names are always
      # kebab-case (no underscores), so the third underscore-split is the param name.
      parts = clean_name.split('_', 3)
      clean_name = parts[3] if len(parts) >= 4 else clean_name

    is_positional = not action.option_strings
    flag = (
      action.option_strings[-1] if action.option_strings else f'--{clean_name.replace("_", "-")}'
    )
    if action.nargs != 0 and getattr(action, 'action', None) != 'store_true':
      metavar = action.metavar or clean_name.upper()
      flag = f'{flag} {metavar}'

    help_text = action.help or ''
    if is_positional:
      required = action.default is None and action.nargs not in ('?', '*')
    else:
      required = bool(getattr(action, 'required', False))
    return flag, help_text, required

  def _extract_options(self, parser: argparse.ArgumentParser) -> list[tuple[str, str, bool]]:
    """Return options for ``parser`` as ``(name, help, required)`` tuples.

    Excludes the auto-generated ``--help`` action and any subparsers action. Sorted
    alphabetically by display name when alphabetization is enabled (default).
    """
    options: list[tuple[str, str, bool]] = []
    if parser is None:
      return options
    for action in parser._actions:
      if action.dest == 'help' or isinstance(action, argparse._SubParsersAction):
        continue
      options.append(self._extract_arg(action))
    if self._alphabetize:
      options.sort(key=lambda row: row[0])
    return options

  def _find_subparsers_action(
    self, parser: argparse.ArgumentParser
  ) -> argparse._SubParsersAction | None:
    """Find the ``_SubParsersAction`` (if any) on a parser."""
    found = None
    for action in parser._actions:
      if isinstance(action, argparse._SubParsersAction):
        found = action
        break
    return found

  def _parser_has_required(self, parser: argparse.ArgumentParser) -> bool:
    """Return True iff ``parser`` (or any nested parser) has at least one required option."""
    has_req = any(required for _, _, required in self._extract_options(parser))
    if not has_req:
      sub_action = self._find_subparsers_action(parser)
      if sub_action is not None:
        has_req = any(
          self._parser_has_required(sub_parser) for sub_parser in sub_action.choices.values()
        )
    return has_req

  def _sorted_subparser_items(
    self, action: argparse._SubParsersAction
  ) -> list[tuple[str, argparse.ArgumentParser, bool]]:
    """Return ``(name, parser, is_system)`` triples sorted system-first, then by name."""
    items: list[tuple[str, argparse.ArgumentParser, bool]] = []
    for name, sub_parser in action.choices.items():
      is_system = bool(getattr(sub_parser, '_is_system_command', False))
      items.append((name, sub_parser, is_system))
    if self._alphabetize:
      items.sort(key=lambda row: (not row[2], row[0]))
    return items

  # ----- rendering ---------------------------------------------------------------------

  def _format_option_action(self, action: argparse.Action) -> str:
    """Render a top-level option row (always at the command-option indent)."""
    name, help_text, required = self._extract_arg(action)
    return '\n'.join(
      self._render_row(
        name=name,
        description=help_text,
        name_indent=INDENT_COMMAND_OPTION,
        name_style='command_group_option_name',
        desc_style='command_group_option_description',
        required=required,
      )
    )

  def _format_subparsers_action(self, action: argparse._SubParsersAction) -> str:
    """Render the COMMANDS section (the top-level subparser tree)."""
    lines: list[str] = []
    has_required = False
    for name, sub_parser, _is_system in self._sorted_subparser_items(action):
      lines.extend(
        self._render_subparser(
          name=name,
          parser=sub_parser,
          base_indent=INDENT_COMMAND,
          name_style='command_group_name',
          opt_style='command_group_option_name',
        )
      )
      if self._parser_has_required(sub_parser):
        has_required = True

    if has_required:
      lines.append('')
      lines.append(self._apply_style('* - required', 'required_asterisk'))
    return '\n'.join(lines)

  def _render_subparser(
    self,
    name: str,
    parser: argparse.ArgumentParser,
    base_indent: int,
    name_style: str,
    opt_style: str,
  ) -> list[str]:
    """Render one subparser: header row, its options, then its nested sub-parsers."""
    lines: list[str] = []

    description = (
      getattr(parser, '_command_group_description', None)
      or parser.description
      or getattr(parser, 'help', '')
      or ''
    )

    lines.extend(
      self._render_row(
        name=name,
        description=description,
        name_indent=base_indent,
        name_style=name_style,
        desc_style=name_style.replace('_name', '_description'),
        add_colon=True,
      )
    )

    opt_indent = base_indent + 4
    opt_desc_style = opt_style.replace('_name', '_description')
    for opt_name, opt_help, required in self._extract_options(parser):
      lines.extend(
        self._render_row(
          name=opt_name,
          description=opt_help,
          name_indent=opt_indent,
          name_style=opt_style,
          desc_style=opt_desc_style,
          required=required,
        )
      )

    nested = self._find_subparsers_action(parser)
    if nested is not None:
      for sub_name, sub_parser, _is_system in self._sorted_subparser_items(nested):
        lines.extend(
          self._render_subparser(
            name=sub_name,
            parser=sub_parser,
            base_indent=base_indent + 2,
            name_style='grouped_command_name',
            opt_style='grouped_command_option_name',
          )
        )
    return lines

  def _render_row(
    self,
    name: str,
    description: str,
    name_indent: int,
    name_style: str,
    desc_style: str,
    required: bool = False,
    add_colon: bool = False,
  ) -> list[str]:
    """Render one help row at the given indent, wrapping with a hanging indent.

    The description column for the row is ``desc_start_col + name_indent``. The first
    line is inline at that column; continuation lines hang-indent at ``desc_col + 4``.
    """
    display_name = f'{name}:' if add_colon else name
    name_visible_w = len(display_name)
    ast_badge = ' *' if required else ''
    ast_visible_w = 2 if required else 0
    desc_col = self._desc_col_for_indent(name_indent)
    # Hanging indent for wrapped continuations. On narrow terminals it can creep past
    # the right margin; cap it so descriptions always have at least 12 chars to wrap.
    cont_col = min(desc_col + 4, max(name_indent + 4, self._console_width - 12))
    cont_avail = max(1, self._console_width - cont_col)

    styled_name = self._apply_style(display_name, name_style)
    styled_ast = self._apply_style(ast_badge, 'required_asterisk') if required else ''

    if not (description or '').strip():
      return [' ' * name_indent + styled_name + styled_ast]

    # If the name (with optional required badge) crowds or overflows the description
    # column, push the description onto the next line at desc_col.
    name_end = name_indent + name_visible_w + ast_visible_w
    overflow = name_end >= desc_col

    wrapped = textwrap.wrap(
      description, width=cont_avail, break_long_words=False, break_on_hyphens=False
    ) or ['']

    lines: list[str] = []
    if overflow:
      lines.append(' ' * name_indent + styled_name)
      for idx, chunk in enumerate(wrapped):
        col = desc_col if idx == 0 else cont_col
        lines.append(' ' * col + self._apply_style(chunk, desc_style))
    else:
      pad_width = desc_col - (name_indent + name_visible_w)
      first_desc = self._apply_style(wrapped[0], desc_style)
      lines.append(' ' * name_indent + styled_name + ' ' * pad_width + first_desc)
      for chunk in wrapped[1:]:
        lines.append(' ' * cont_col + self._apply_style(chunk, desc_style))

    # Required-badge always tags the final rendered line so it stays adjacent to the
    # full description, regardless of wrapping.
    if required and lines:
      lines[-1] = lines[-1] + styled_ast
    return lines

  # ----- styling helper ----------------------------------------------------------------

  def _apply_style(self, text: str, style_name: str) -> str:
    """Apply a named ThemeStyle to ``text`` via the color formatter."""
    if not text:
      return text
    theme = self._freyja_theme
    style_map = {
      'title': theme.title,
      'subtitle': theme.subtitle,
      'required_asterisk': theme.required_asterisk,
      'command_output': theme.command_output,
      'command_group_name': theme.command_group_section.command_name,
      'command_group_description': theme.command_group_section.command_description,
      'command_group_option_name': theme.command_group_section.option_name,
      'command_group_option_description': theme.command_group_section.option_description,
      'grouped_command_name': theme.grouped_command_section.command_name,
      'grouped_command_description': theme.grouped_command_section.command_description,
      'grouped_command_option_name': theme.grouped_command_section.option_name,
      'grouped_command_option_description': theme.grouped_command_section.option_description,
    }
    style = style_map.get(style_name)
    return self._color_formatter.apply_style(text, style) if style is not None else text
