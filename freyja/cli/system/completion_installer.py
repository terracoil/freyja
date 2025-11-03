"""Shell completion installation functionality."""

import os
import sys
import subprocess
from pathlib import Path


class CompletionInstaller:
  """Handles installation of shell completion scripts for Freyja CLIs."""

  def __init__(
    self,
    handler,
    prog_name: str,
    command_patterns: list[str] | None = None
  ) -> None:
    """Initialize completion installer with handler and program name.

    :param handler: Completion handler for specific shell
    :param prog_name: Program name for completion (normalized to basename)
    :param command_patterns: Additional command patterns to register completion for
    """
    self.handler = handler
    self.prog_name = Path(prog_name).name
    self.command_patterns = command_patterns or []
    self.shell = self._detect_shell()

  def install(self, shell: str | None = None, force: bool = False) -> bool:
    """Install completion for specified or detected shell.

    :param shell: Target shell (auto-detect if None)
    :param force: Force overwrite existing completion
    :return: True if installation successful
    """
    target_shell = shell or self.shell
    result = False

    if not target_shell:
      print("Could not detect shell. Please specify shell manually.", file=sys.stderr)
    elif target_shell == "bash":
      result = self._install_bash_completion(force)
    elif target_shell == "zsh":
      result = self._install_zsh_completion(force)
    elif target_shell == "fish":
      result = self._install_fish_completion(force)
    else:
      print(f"Unsupported shell: {target_shell}", file=sys.stderr)

    return result

  def _detect_shell(self) -> str:
    """Detect the current shell from environment."""
    shell_env = os.environ.get("SHELL", "")
    result = "bash"  # Default fallback

    if "zsh" in shell_env:
      result = "zsh"
    elif "fish" in shell_env:
      result = "fish"

    return result

  def _install_bash_completion(self, force: bool) -> bool:
    """Install bash completion script."""
    completion_dir = Path.home() / ".bash_completion.d"
    completion_dir.mkdir(parents=True, exist_ok=True)

    completion_file = completion_dir / f"{self.prog_name}_completion"
    success = False

    if completion_file.exists() and not force:
      print(f"Completion already exists at {completion_file}. Use --force to overwrite.")
    else:
      try:
        script = self.handler.generate_script(self.prog_name)
        completion_file.write_text(script)
        self._update_bashrc(completion_file)
        print(f"Bash completion installed to {completion_file}")
        print("Restart your shell or run: source ~/.bashrc")
        success = True
      except Exception as e:
        print(f"Error installing bash completion: {e}", file=sys.stderr)

    return success

  def _install_zsh_completion(self, force: bool) -> bool:
    """Install zsh completion script."""
    completion_dir = Path.home() / ".zfunc"
    completion_dir.mkdir(parents=True, exist_ok=True)

    completion_file = completion_dir / f"_{self.prog_name}"
    success = False

    if completion_file.exists() and not force:
      print(f"Completion already exists at {completion_file}. Use --force to overwrite.")
    else:
      try:
        script = self.handler.generate_script(self.prog_name, self.command_patterns)
        completion_file.write_text(script)
        self._configure_zsh_fpath(completion_dir)
        print(f"Zsh completion installed to {completion_file}")
        print("Restart your shell or run: source ~/.zshrc && autoload -U compinit && compinit")
        success = True
      except Exception as e:
        print(f"Error installing zsh completion: {e}", file=sys.stderr)

    return success

  def _install_fish_completion(self, force: bool) -> bool:
    """Install fish completion script."""
    completion_dir = Path.home() / ".config" / "fish" / "completions"
    completion_dir.mkdir(parents=True, exist_ok=True)

    completion_file = completion_dir / f"{self.prog_name}.fish"
    success = False

    if completion_file.exists() and not force:
      print(f"Completion already exists at {completion_file}. Use --force to overwrite.")
    else:
      try:
        script = self.handler.generate_script(self.prog_name)
        completion_file.write_text(script)
        print(f"Fish completion installed to {completion_file}")
        print("Restart your shell for changes to take effect")
        success = True
      except Exception as e:
        print(f"Error installing fish completion: {e}", file=sys.stderr)

    return success

  def _update_bashrc(self, completion_file: Path) -> None:
    """Add completion sourcing to .bashrc if not already present."""
    bashrc = Path.home() / ".bashrc"
    source_line = f'source "{completion_file}"'

    if bashrc.exists():
      bashrc_content = bashrc.read_text()
      if source_line not in bashrc_content:
        with open(bashrc, "a") as f:
          f.write(f"\n# Freyja completion for {self.prog_name}\n")
          f.write(f"{source_line}\n")

  def _configure_zsh_fpath(self, completion_dir: Path) -> None:
    """Configure zsh fpath if needed."""
    needs_fpath_config = True

    try:
      result = subprocess.run(
        ["/bin/zsh", "-c", "echo $fpath"],
        capture_output=True,
        text=True
      )
      if completion_dir.as_posix() in result.stdout:
        needs_fpath_config = False
    except (subprocess.SubprocessError, OSError):
      pass  # Assume we need to configure fpath

    if needs_fpath_config:
      zshrc_path = Path.home() / ".zshrc"
      fpath_line = f"fpath=({completion_dir} $fpath)"

      try:
        if zshrc_path.exists():
          zshrc_content = zshrc_path.read_text()
          if str(completion_dir) not in zshrc_content:
            with open(zshrc_path, "a") as f:
              f.write("\n# Freyja completion directory\n")
              f.write(f"{fpath_line}\n")
        else:
          with open(zshrc_path, "w") as f:
            f.write("# Freyja completion directory\n")
            f.write(f"{fpath_line}\n")
      except Exception:
        print(f"\nAdd this line to your ~/.zshrc:\n{fpath_line}")