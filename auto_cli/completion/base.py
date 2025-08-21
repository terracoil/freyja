"""Base classes and data structures for shell completion."""

import argparse
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional, Type, Union

from .. import CLI


@dataclass
class CompletionContext:
    """Context information for generating completions."""
    words: List[str]              # All words in current command line
    current_word: str             # Word being completed (partial)
    cursor_position: int          # Position in current word
    subcommand_path: List[str]    # Path to current subcommand (e.g., ['db', 'backup'])
    parser: argparse.ArgumentParser  # Current parser context
    cli: CLI                      # CLI instance for introspection


class CompletionHandler(ABC):
    """Abstract base class for shell-specific completion handlers."""
    
    def __init__(self, cli: CLI):
        """Initialize completion handler with CLI instance.
        
        :param cli: CLI instance to provide completion for
        """
        self.cli = cli
    
    @abstractmethod
    def generate_script(self, prog_name: str) -> str:
        """Generate shell-specific completion script.
        
        :param prog_name: Program name for completion
        :return: Shell-specific completion script
        """
    
    @abstractmethod
    def get_completions(self, context: CompletionContext) -> List[str]:
        """Get completions for current context.
        
        :param context: Completion context with current state
        :return: List of completion suggestions
        """
    
    @abstractmethod
    def install_completion(self, prog_name: str) -> bool:
        """Install completion for current shell.
        
        :param prog_name: Program name to install completion for
        :return: True if installation successful
        """
    
    def detect_shell(self) -> Optional[str]:
        """Detect current shell from environment."""
        shell = os.environ.get('SHELL', '')
        if 'bash' in shell:
            return 'bash'
        elif 'zsh' in shell:
            return 'zsh'  
        elif 'fish' in shell:
            return 'fish'
        elif os.name == 'nt' or 'pwsh' in shell or 'powershell' in shell:
            return 'powershell'
        return None
    
    def get_subcommand_parser(self, parser: argparse.ArgumentParser, 
                            subcommand_path: List[str]) -> Optional[argparse.ArgumentParser]:
        """Navigate to subcommand parser following the path.
        
        :param parser: Root parser to start from
        :param subcommand_path: Path to target subcommand
        :return: Target parser or None if not found
        """
        current_parser = parser
        
        for subcommand in subcommand_path:
            found_parser = None
            
            # Look for subcommand in parser actions
            for action in current_parser._actions:
                if isinstance(action, argparse._SubParsersAction):
                    if subcommand in action.choices:
                        found_parser = action.choices[subcommand]
                        break
            
            if not found_parser:
                return None
            
            current_parser = found_parser
        
        return current_parser
    
    def get_available_commands(self, parser: argparse.ArgumentParser) -> List[str]:
        """Get list of available commands from parser.
        
        :param parser: Parser to extract commands from
        :return: List of command names
        """
        commands = []
        
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                commands.extend(action.choices.keys())
        
        return commands
    
    def get_available_options(self, parser: argparse.ArgumentParser) -> List[str]:
        """Get list of available options from parser.
        
        :param parser: Parser to extract options from
        :return: List of option names (with -- prefix)
        """
        options = []
        
        for action in parser._actions:
            if action.option_strings:
                # Add long options (prefer --option over -o)
                for option_string in action.option_strings:
                    if option_string.startswith('--'):
                        options.append(option_string)
                        break
        
        return options
    
    def get_option_values(self, parser: argparse.ArgumentParser, 
                         option_name: str, partial: str = "") -> List[str]:
        """Get possible values for a specific option.
        
        :param parser: Parser containing the option
        :param option_name: Option to get values for (with -- prefix) 
        :param partial: Partial value being completed
        :return: List of possible values
        """
        for action in parser._actions:
            if option_name in action.option_strings:
                # Handle enum choices
                if hasattr(action, 'choices') and action.choices:
                    if hasattr(action.choices, '__iter__'):
                        # For enum types, get the names
                        try:
                            choices = [choice.name for choice in action.choices]
                            return self.complete_partial_word(choices, partial)
                        except AttributeError:
                            # Regular choices list
                            choices = list(action.choices)
                            return self.complete_partial_word(choices, partial)
                
                # Handle boolean flags
                if getattr(action, 'action', None) == 'store_true':
                    return []  # No completions for boolean flags
                
                # Handle file paths
                if getattr(action, 'type', None):
                    type_name = getattr(action.type, '__name__', str(action.type))
                    if 'Path' in type_name or action.type == str:
                        return self._complete_file_path(partial)
        
        return []
    
    def _complete_file_path(self, partial: str) -> List[str]:
        """Complete file paths.
        
        :param partial: Partial path being completed
        :return: List of matching paths
        """
        import glob
        import os
        
        if not partial:
            # No partial path, return current directory contents
            try:
                return sorted([f for f in os.listdir('.') 
                             if not f.startswith('.')])[:10]  # Limit results
            except (OSError, PermissionError):
                return []
        
        # Expand partial path with glob
        try:
            # Handle different path patterns
            if partial.endswith('/') or partial.endswith(os.sep):
                # Complete directory contents
                pattern = partial + '*'
            else:
                # Complete partial filename/dirname
                pattern = partial + '*'
            
            matches = glob.glob(pattern)
            
            # Limit and sort results
            matches = sorted(matches)[:10]
            
            # Add trailing slash for directories
            result = []
            for match in matches:
                if os.path.isdir(match):
                    result.append(match + os.sep)
                else:
                    result.append(match)
            
            return result
            
        except (OSError, PermissionError):
            return []
    
    def complete_partial_word(self, candidates: List[str], partial: str) -> List[str]:
        """Filter candidates based on partial word match.
        
        :param candidates: List of possible completions
        :param partial: Partial word to match against
        :return: Filtered list of completions
        """
        if not partial:
            return candidates
        
        return [candidate for candidate in candidates 
                if candidate.startswith(partial)]