"""Text-based spinner with status display for command execution."""

import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CommandContext:
    """Context for command execution display."""
    namespace: Optional[str] = None
    command: str = ""
    subcommand: Optional[str] = None
    global_args: Dict[str, Any] = field(default_factory=dict)
    group_args: Dict[str, Any] = field(default_factory=dict)
    command_args: Dict[str, Any] = field(default_factory=dict)
    positional_args: List[Any] = field(default_factory=list)
    custom_status: Optional[str] = None


class ExecutionSpinner:
    """Manages spinner and status display during command execution."""
    
    def __init__(self, color_formatter=None, verbose: bool = False):
        """Initialize the execution spinner.
        
        :param color_formatter: ColorFormatter instance for styling
        :param verbose: Whether to run in verbose mode
        """
        self.color_formatter = color_formatter
        self.verbose = verbose
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current = 0
        self.running = False
        self.thread = None
        self.command_context: Optional[CommandContext] = None
        self.status_line = ""
        self._lock = threading.Lock()
        
    def augment_status(self, custom_status: str):
        """Add custom status to the display.
        
        :param custom_status: Custom status message to append
        """
        with self._lock:
            if self.command_context:
                self.command_context.custom_status = custom_status
                self._update_status_line()
    
    def _format_command_name(self) -> str:
        """Format command name based on context.
        
        :return: Formatted command name string
        """
        if not self.command_context:
            return ""
        
        parts = []
        if self.command_context.namespace:
            parts.append(self.command_context.namespace)
        parts.append(self.command_context.command)
        
        if self.command_context.subcommand:
            return f"{':'.join(parts)}:{self.command_context.subcommand}"
        return ':'.join(parts) if parts else ""
    
    def _format_options(self) -> List[str]:
        """Format all options for display.
        
        :return: List of formatted option strings
        """
        if not self.command_context:
            return []
        
        options = []
        
        # Positional arguments first
        for i, arg in enumerate(self.command_context.positional_args):
            options.append(f"positional:{i}:{arg}")
        
        # Global arguments
        for key, value in self.command_context.global_args.items():
            options.append(f"global:{key}:{value}")
        
        # Group arguments  
        for key, value in self.command_context.group_args.items():
            group_name = self.command_context.namespace or "group"
            options.append(f"{group_name}:{key}:{value}")
        
        # Command arguments
        for key, value in self.command_context.command_args.items():
            command_name = self.command_context.command or "command"
            options.append(f"{command_name}:{key}:{value}")
        
        return options
    
    def _update_status_line(self):
        """Update the status line based on current context."""
        if not self.command_context:
            self.status_line = ""
            return
        
        command_display = self._format_command_name()
        status_parts = [f"Executing {command_display}"]
        
        options = self._format_options()
        if options:
            # Limit options display to avoid overly long lines
            if len(options) <= 3:
                status_parts.append(f"[{', '.join(options)}]")
            else:
                shown_options = options[:2]
                remaining = len(options) - 2
                shown_options.append(f"... +{remaining} more")
                status_parts.append(f"[{', '.join(shown_options)}]")
        
        if self.command_context.custom_status:
            status_parts.append(f"→ {self.command_context.custom_status}")
        
        self.status_line = " ".join(status_parts)
    
    def start(self, command_context: CommandContext):
        """Start the spinner with given context.
        
        :param command_context: CommandContext with execution details
        """
        with self._lock:
            self.command_context = command_context
            self._update_status_line()
            
            if self.verbose:
                # In verbose mode, just print the status once
                if self.color_formatter and hasattr(self.color_formatter, 'apply_style'):
                    # Apply command_output styling if available
                    try:
                        from ..theme.theme_style import ThemeStyle
                        from ..theme.defaults import create_default_theme
                        theme = create_default_theme()
                        styled_line = self.color_formatter.apply_style(self.status_line, theme.command_output)
                        print(styled_line)
                    except Exception:
                        # Fall back to plain text if styling fails
                        print(self.status_line)
                else:
                    print(self.status_line)
                return
            
            # Non-verbose mode: start spinner thread
            self.running = True
            self.thread = threading.Thread(target=self._spin)
            self.thread.daemon = True
            self.thread.start()
    
    def _spin(self):
        """Spinner animation loop (runs in separate thread)."""
        while self.running:
            with self._lock:
                current_status = self.status_line
                char = self.spinner_chars[self.current]
            
            # Write spinner and status
            sys.stdout.write(f"\r{char} {current_status}")
            sys.stdout.flush()
            
            self.current = (self.current + 1) % len(self.spinner_chars)
            time.sleep(0.1)
    
    def stop(self, success: bool = True):
        """Stop the spinner.
        
        :param success: Whether the command succeeded
        """
        with self._lock:
            self.running = False
            
            if self.thread:
                # Wait for spinner thread to finish
                self.thread.join(timeout=0.5)
            
            if not self.verbose:
                # Clear the spinner line
                line_length = len(self.status_line) + 3  # spinner char + space + space
                sys.stdout.write("\r" + " " * line_length + "\r")
                sys.stdout.flush()
                
                # Print final status if failed or verbose
                if not success:
                    status_char = "✗"
                    final_status = f"{status_char} {self.status_line}"
                    
                    if self.color_formatter and hasattr(self.color_formatter, 'apply_style'):
                        try:
                            from ..theme.theme_style import ThemeStyle
                            from ..theme.defaults import create_default_theme
                            theme = create_default_theme()
                            styled_status = self.color_formatter.apply_style(final_status, theme.command_output)
                            print(styled_status)
                        except Exception:
                            print(final_status)
                    else:
                        print(final_status)
    
    @contextmanager
    def execute(self, command_context: CommandContext):
        """Context manager for command execution with spinner.
        
        :param command_context: CommandContext with execution details
        """
        self.start(command_context)
        success = True
        try:
            yield self
        except Exception:
            success = False
            raise
        finally:
            self.stop(success)