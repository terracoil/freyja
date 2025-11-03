"""Completion installation and management."""

import os
import sys
from pathlib import Path

from .base import CompletionHandler


class CompletionInstaller:
    """Handles installation of shell completion scripts."""

    def __init__(
        self, handler: CompletionHandler, prog_name: str, command_patterns: list | None = None
    ):
        """Initialize installer with handler and program name.

        :param handler: Completion handler for specific shell
        :param prog_name: Program name for completion (normalized to basename)
        :param command_patterns: Additional command patterns to register completion for
        """
        from pathlib import Path

        self.handler = handler
        # Normalize program name to basename to handle path-based invocations
        # Ensures examples/cls_example → cls_example for consistent registration
        self.prog_name = Path(prog_name).name
        self.command_patterns = command_patterns or []
        self.shell = handler.detect_shell()

    # Supported shell installers mapping
    _SHELL_INSTALLERS = {
        "bash": "_install_bash_completion",
        "zsh": "_install_zsh_completion",
        "fish": "_install_fish_completion",
        "powershell": "_install_powershell_completion",
    }

    def install(self, shell: str | None = None, force: bool = False) -> bool:
        """Install completion for specified or detected shell.

        :param shell: Target shell (auto-detect if None)
        :param force: Force overwrite existing completion
        :return: True if installation successful
        """
        # Guard: Ensure shell is detected
        target_shell = shell or self.shell
        if not target_shell:
            raise ValueError("Could not detect shell. Please specify shell manually.")
        
        # Guard: Ensure shell is supported
        if target_shell not in self._SHELL_INSTALLERS:
            raise ValueError(f"Unsupported shell: {target_shell}")
        
        installer_method_name = self._SHELL_INSTALLERS[target_shell]
        installer_method = getattr(self, installer_method_name)
        return installer_method(force)

    def _install_bash_completion(self, force: bool) -> bool:
        """Install bash completion."""
        # Try user completion directory first
        completion_dir = Path.home() / ".bash_completion.d"
        if not completion_dir.exists():
            completion_dir.mkdir(parents=True, exist_ok=True)

        completion_file = completion_dir / f"{self.prog_name}_completion"

        # Check if already exists
        if completion_file.exists() and not force:
            print(f"Completion already exists at {completion_file}. Use --force to overwrite.")
            return False

        # Generate and write completion script
        script = self.handler.generate_script(self.prog_name)
        completion_file.write_text(script)

        # Add sourcing to .bashrc if not already present
        bashrc = Path.home() / ".bashrc"
        source_line = f'source "{completion_file}"'

        if bashrc.exists():
            bashrc_content = bashrc.read_text()
            if source_line not in bashrc_content:
                with open(bashrc, "a") as f:
                    f.write(f"\n# Freyja completion for {self.prog_name}\n")
                    f.write(f"{source_line}\n")
                print(f"Added completion sourcing to {bashrc}")

        print(f"Bash completion installed to {completion_file}")
        print("Restart your shell or run: source ~/.bashrc")
        return True

    def _install_zsh_completion(self, force: bool) -> bool:
        """Install zsh completion."""
        # Try standard user completion directories in order of preference
        completion_dirs = [
            Path.home() / ".zfunc",  # Most standard location
            Path.home() / ".zsh" / "completions",
        ]

        # Use first directory that exists or can be created
        completion_dir = None
        for dir_path in completion_dirs:
            if dir_path.exists():
                completion_dir = dir_path
                break
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                completion_dir = dir_path
                break
            except (OSError, PermissionError):
                continue

        if not completion_dir:
            completion_dir = completion_dirs[0]  # Default to .zfunc
        completion_dir.mkdir(parents=True, exist_ok=True)
        completion_file = completion_dir / f"_{self.prog_name}"

        # Check if already exists
        if completion_file.exists() and not force:
            print(f"Completion already exists at {completion_file}. Use --force to overwrite.")
            return False

        # Generate and write completion script with command patterns
        # Check if handler supports command_patterns parameter
        import inspect
        sig = inspect.signature(self.handler.generate_script)
        if len(sig.parameters) > 1:  # Has command_patterns parameter
            script = self.handler.generate_script(self.prog_name, self.command_patterns)
        else:  # Only supports prog_name
            script = self.handler.generate_script(self.prog_name)
        completion_file.write_text(script)

        print(f"Zsh completion installed to {completion_file}")

        # Clear completion cache to ensure new completions are loaded
        zcompdump_files = [
            Path.home() / ".zcompdump",
            Path.home() / f'.zcompdump-{os.getenv("HOST", "")}-{os.getenv("ZSH_VERSION", "")}',
        ]

        for zcompdump_file in zcompdump_files:
            if zcompdump_file.exists():
                try:
                    zcompdump_file.unlink()
                    print(f"Cleared completion cache: {zcompdump_file}")
                except (OSError, PermissionError):
                    pass  # Ignore if we can't remove it

        # Check if completion directory is in fpath and auto-configure if needed
        import subprocess

        needs_fpath_config = True
        try:
            result = subprocess.run(
                ["/bin/zsh", "-c", "echo $fpath"], capture_output=True, text=True
            )
            if completion_dir.as_posix() in result.stdout:
                needs_fpath_config = False
        except (subprocess.SubprocessError, OSError):
            pass  # Assume we need to configure fpath

        if needs_fpath_config:
            # Try to automatically add fpath configuration to ~/.zshrc
            zshrc_path = Path.home() / ".zshrc"
            fpath_line = f"fpath=({completion_dir} $fpath)"

            try:
                if zshrc_path.exists():
                    zshrc_content = zshrc_path.read_text()
                    # Check if fpath line already exists in some form
                    if str(completion_dir) not in zshrc_content or "fpath=" not in zshrc_content:
                        with open(zshrc_path, "a") as f:
                            f.write("\n# Freyja completion directory\n")
                            f.write(f"{fpath_line}\n")
                        print(f"Added fpath configuration to {zshrc_path}")
                    else:
                        print(f"fpath already configured in {zshrc_path}")
                else:
                    # Create .zshrc with fpath configuration
                    with open(zshrc_path, "w") as f:
                        f.write("# Freyja completion directory\n")
                        f.write(f"{fpath_line}\n")
                    print(f"Created {zshrc_path} with fpath configuration")

                print(
                    "Restart your shell or run: source ~/.zshrc && autoload -U compinit && compinit"
                )
            except Exception:
                print("\nCould not configure fpath. Add this line to your ~/.zshrc:")
                print(f"{fpath_line}")
                print("Then run: autoload -U compinit && compinit")
        else:
            print("fpath already configured. Run: autoload -U compinit && compinit")

        return True

    def _install_fish_completion(self, force: bool) -> bool:
        """Install fish completion."""
        completion_dir = Path.home() / ".config" / "fish" / "completions"
        completion_dir.mkdir(parents=True, exist_ok=True)

        completion_file = completion_dir / f"{self.prog_name}.fish"

        # Check if already exists
        if completion_file.exists() and not force:
            print(f"Completion already exists at {completion_file}. Use --force to overwrite.")
            return False

        # Generate and write completion script
        script = self.handler.generate_script(self.prog_name)
        completion_file.write_text(script)

        print(f"Fish completion installed to {completion_file}")
        print("Restart your shell for changes to take effect")
        return True

    def _install_powershell_completion(self, force: bool) -> bool:
        """Install PowerShell completion."""
        # PowerShell profile path
        if os.name == "nt":
            # Windows PowerShell
            profile_dir = (
                Path(os.environ.get("USERPROFILE", "")) / "Documents" / "WindowsPowerShell"
            )
        else:
            # PowerShell Core on Unix
            profile_dir = Path.home() / ".config" / "powershell"

        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profile_dir / "Microsoft.PowerShell_profile.ps1"

        # Generate completion script
        script = self.handler.generate_script(self.prog_name)

        # Check if profile exists and has our completion
        completion_marker = f"# Freyja completion for {self.prog_name}"

        if profile_file.exists():
            profile_content = profile_file.read_text()
            if completion_marker in profile_content and not force:
                print(f"Completion already installed in {profile_file}. Use --force to overwrite.")
                return False

            # Remove old completion if forcing
            if force and completion_marker in profile_content:
                lines = profile_content.split("\n")
                new_lines = []
                skip_next = False

                for line in lines:
                    if completion_marker in line:
                        skip_next = True
                        continue
                    if skip_next and line.strip().startswith("Register-ArgumentCompleter"):
                        skip_next = False
                        continue
                    new_lines.append(line)

                profile_content = "\n".join(new_lines)
        else:
            profile_content = ""

        # Add completion to profile
        with open(profile_file, "w") as f:
            f.write(profile_content)
            f.write(f"\n{completion_marker}\n")
            f.write(script)

        print(f"PowerShell completion installed to {profile_file}")
        print("Restart PowerShell for changes to take effect")
        return True

    def uninstall(self, shell: str | None = None) -> bool:
        """Remove installed completion.

        :param shell: Target shell (auto-detect if None)
        :return: True if uninstallation successful
        """
        target_shell = shell or self.shell

        if not target_shell:
            print("Could not detect shell. Please specify shell manually.", file=sys.stderr)
            return False

        success = False

        if target_shell == "bash":
            completion_file = Path.home() / ".bash_completion.d" / f"{self.prog_name}_completion"
            if completion_file.exists():
                completion_file.unlink()
                success = True

        elif target_shell == "zsh":
            completion_dirs = [
                Path.home() / ".zsh" / "completions",
                Path.home() / ".oh-my-zsh" / "completions",
                Path("/usr/local/share/zsh/site-functions"),
            ]

            for dir_path in completion_dirs:
                completion_file = dir_path / f"_{self.prog_name}"
                if completion_file.exists():
                    completion_file.unlink()
                    success = True

        elif target_shell == "fish":
            completion_file = (
                Path.home() / ".config" / "fish" / "completions" / f"{self.prog_name}.fish"
            )
            if completion_file.exists():
                completion_file.unlink()
                success = True

        elif target_shell == "powershell":
            # For PowerShell, we would need to edit the profile file
            print("PowerShell completion uninstall requires manual removal from profile.")
            return False

        if success:
            print(f"Completion uninstalled for {target_shell}")
        else:
            print(f"No completion found to uninstall for {target_shell}")

        return success
