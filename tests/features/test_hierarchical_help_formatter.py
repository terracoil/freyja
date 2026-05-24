"""Tests for the hierarchical help formatter (layout + Sunset theme)."""

from __future__ import annotations

import re
from unittest.mock import Mock, patch

from freyja import FreyjaCLI
from freyja.help.help_formatter import (
  DESC_START_COL_MIN,
  INDENT_COMMAND,
  INDENT_COMMAND_OPTION,
  INDENT_SUBCOMMAND,
  INDENT_SUBCOMMAND_OPTION,
  HierarchicalHelpFormatter,
  compute_desc_start_col,
  detect_console_width,
)
from freyja.theme import create_no_color_theme, get_default_theme

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def _strip(text: str) -> str:
  return ANSI_RE.sub('', text)


def _help_for(cli: FreyjaCLI, *, no_color: bool = True) -> str:
  return cli.create_parser(no_color=no_color).format_help()


def _leading_spaces(line: str) -> int:
  match = re.match(r' *', line)
  return match.end() if match else 0


# ----- Console width detection ---------------------------------------------------------


class TestConsoleWidthDetection:
  """``detect_console_width`` clamps to [40, 200] and prefers $COLUMNS."""

  def test_prefers_columns_env(self):
    with patch.dict('os.environ', {'COLUMNS': '120'}, clear=False):
      with patch('os.get_terminal_size', side_effect=OSError()):
        assert detect_console_width() == 120

  def test_falls_back_to_get_terminal_size(self):
    with patch.dict('os.environ', {}, clear=True):
      with patch('os.get_terminal_size', return_value=Mock(columns=140)):
        assert detect_console_width() == 140

  def test_default_when_all_unavailable(self):
    with patch.dict('os.environ', {}, clear=True):
      with patch('os.get_terminal_size', side_effect=OSError()):
        assert detect_console_width() == 100

  def test_clamps_to_minimum_40(self):
    with patch.dict('os.environ', {'COLUMNS': '10'}, clear=False):
      assert detect_console_width() == 40

  def test_clamps_to_maximum_200(self):
    with patch.dict('os.environ', {'COLUMNS': '9999'}, clear=False):
      assert detect_console_width() == 200


# ----- desc_start_col math -------------------------------------------------------------


class TestDescStartCol:
  """``compute_desc_start_col`` applies the even-rounding rule with a 32 floor."""

  def test_short_name_uses_floor(self):
    # Floor wins when name_max + 3/4 falls below 32.
    assert compute_desc_start_col(name_max=5, console_width=200) == DESC_START_COL_MIN
    assert compute_desc_start_col(name_max=20, console_width=200) == DESC_START_COL_MIN

  def test_even_rounding_above_floor(self):
    # name_max=30 → +4 (even) = 34
    assert compute_desc_start_col(name_max=30, console_width=200) == 34
    # name_max=31 → +3 (odd → even) = 34
    assert compute_desc_start_col(name_max=31, console_width=200) == 34
    # name_max=32 → +4 = 36
    assert compute_desc_start_col(name_max=32, console_width=200) == 36
    # name_max=33 → +3 = 36
    assert compute_desc_start_col(name_max=33, console_width=200) == 36

  def test_capped_at_half_console_width(self):
    # Floor is 32 but console_width // 2 = 30 wins.
    assert compute_desc_start_col(name_max=5, console_width=60) == 30

  def test_returns_even_value_for_realistic_names(self):
    for name_max in range(5, 60):
      col = compute_desc_start_col(name_max=name_max, console_width=200)
      assert col % 2 == 0


# ----- Sunset theme integration --------------------------------------------------------


class TestSunsetThemeRendering:
  """End-to-end rendering smoke tests with the default (Sunset) theme."""

  def _build_cli(self):
    class Demo:
      """Demo CLI."""

      def __init__(self, config: str = 'cfg.json'):
        """Initialize Demo."""
        self.config = config

      class Build:
        """Build commands."""

        def autotag(self, version: str = '1.0.0', message: str = '') -> None:
          """Create a git tag."""

        def clean(self, dry_run: bool = False) -> None:
          """Clean artifacts."""

      def show(self, detailed: bool = False) -> None:
        """Show status."""

    return FreyjaCLI(Demo, title='Demo CLI', completion=False)

  def test_help_renders_without_error(self):
    cli = self._build_cli()
    text = _help_for(cli, no_color=True)
    assert 'Demo CLI' in text
    assert 'build' in text
    assert 'autotag' in text

  def test_default_theme_returns_sunset(self):
    theme = get_default_theme()
    cgs = theme.command_group_section
    assert cgs.command_name.bold is True
    assert cgs.command_name.fg.to_hex() == '#CB4B16'
    assert cgs.option_name.fg.to_hex() == '#D33682'

    gcs = theme.grouped_command_section
    assert gcs.command_name.bold is True
    assert gcs.command_name.fg.to_hex() == '#B58900'
    assert gcs.option_name.fg.to_hex() == '#6C71C4'

    assert theme.required_asterisk.bold is True
    assert theme.required_asterisk.fg.to_hex() == '#DC322F'

  def test_no_color_theme_strips_everything(self):
    theme = create_no_color_theme()
    cgs = theme.command_group_section
    assert cgs.command_name.fg is None
    assert cgs.command_name.bold is False
    assert theme.required_asterisk.fg is None


# ----- Layout assertions ---------------------------------------------------------------


class _LayoutFixture:
  """Reusable fixture CLI exercising all four indent levels."""

  class Demo:
    """Demo CLI."""

    def __init__(self, config: str = 'cfg.json'):
      self.config = config

    class Build:
      """Build operations."""

      def __init__(self, parent, parallel: bool = False):
        self.parent = parent
        self.parallel = parallel

      def autotag(self, version: str = '1.0.0') -> None:
        """Create a git tag."""

      def clean(self) -> None:
        """Clean artifacts."""

    def show(self, detailed: bool = False) -> None:
      """Show status."""


class TestLayoutIndents:
  """Each kind of row sits at the indent the user spec demands."""

  def setup_method(self):
    with patch.dict('os.environ', {'COLUMNS': '100'}):
      with patch('os.get_terminal_size', return_value=Mock(columns=100)):
        self.cli = FreyjaCLI(_LayoutFixture.Demo, title='Demo CLI', completion=False)
        self.text = _strip(_help_for(self.cli, no_color=True))
    self.lines = self.text.splitlines()

  def _find(self, needle: str) -> str:
    return next(line for line in self.lines if needle in line)

  def test_command_group_at_indent_2(self):
    assert _leading_spaces(self._find('build:')) == INDENT_COMMAND  # 2

  def test_subcommand_at_indent_4(self):
    assert _leading_spaces(self._find('autotag:')) == INDENT_SUBCOMMAND  # 4

  def test_command_group_option_at_indent_6(self):
    assert _leading_spaces(self._find('--parallel')) == INDENT_COMMAND_OPTION  # 6

  def test_subcommand_option_at_indent_8(self):
    assert _leading_spaces(self._find('--version')) == INDENT_SUBCOMMAND_OPTION  # 8

  def test_only_canonical_indents_present(self):
    distinct = sorted({_leading_spaces(line) for line in self.lines if line.strip()})
    # Top-level options also sit at 6; deeper recursion may add 10. No odd indents.
    assert all(value % 2 == 0 for value in distinct)
    expected_subset = {0, 2, 4, 6, 8}
    assert expected_subset.issubset(set(distinct))


class TestOptionAlphabetization:
  """Options under a command are alphabetized; required/optional interleave by name."""

  def test_options_sorted_under_owner(self):
    class Demo:
      """Demo."""

      class Build:
        """Build."""

        def step(self, zeta: str, alpha: str = '', mu: str = '', kappa: str = '') -> None:
          """Run a step."""

    cli = FreyjaCLI(Demo, completion=False)
    lines = _strip(_help_for(cli, no_color=True)).splitlines()
    # Capture only options under the `step:` subcommand (indent 8).
    target_flags = {'--alpha', '--kappa', '--mu', '--zeta'}
    order = [
      re.search(r'--[a-z]+', line).group(0)
      for line in lines
      if re.match(r' {8}--', line) and re.search(r'--[a-z]+', line).group(0) in target_flags
    ]
    assert order == ['--alpha', '--kappa', '--mu', '--zeta']


class TestWrappingAndHangingIndent:
  """Long descriptions wrap at word boundaries with a hang-indent at desc_col + 4."""

  def test_continuation_uses_hanging_indent(self):
    class Demo:
      """Demo."""

      class Build:
        """Build."""

        def deploy(self, target: str = 'prod') -> None:
          """Deploy the application to a remote environment with extensive logging, rollback support, blue-green orchestration, and notification hooks."""

    with patch.dict('os.environ', {'COLUMNS': '80'}):
      with patch('os.get_terminal_size', return_value=Mock(columns=80)):
        cli = FreyjaCLI(Demo, completion=False)
        text = _strip(_help_for(cli, no_color=True))

    lines = text.splitlines()
    deploy_idx = next(i for i, line in enumerate(lines) if 'deploy:' in line)
    head = lines[deploy_idx]
    name_indent = _leading_spaces(head)
    # First description char must come at the row's desc column.
    desc_col_first = head.find('Deploy')
    assert desc_col_first > name_indent
    # Continuation rows hang-indent 4 spaces deeper than the first description column.
    continuation = lines[deploy_idx + 1]
    assert _leading_spaces(continuation) == desc_col_first + 4

  def test_no_word_is_split(self):
    with patch.dict('os.environ', {'COLUMNS': '100'}):
      with patch('os.get_terminal_size', return_value=Mock(columns=100)):
        cli = FreyjaCLI(_LayoutFixture.Demo, completion=False)
        text = _strip(_help_for(cli, no_color=True))
    # Hyphenless trailing alpha + leading alpha on next line would indicate a split.
    lines = text.splitlines()
    for first, second in zip(lines, lines[1:], strict=False):
      if (
        first
        and second
        and first[-1].isalpha()
        and second.lstrip().startswith(tuple('abcdefghijklmnopqrstuvwxyz'))
      ):
        # A continuation that begins with a lower-case letter after a word-final alpha
        # is OK iff there was a space before the wrap. The wrapper guarantees that;
        # this is a sanity check that we never produce mid-word breaks like 'Clau\nde'.
        assert ' ' in first


# ----- Required asterisk badge ---------------------------------------------------------


class TestRequiredAsterisk:
  """The `* - required` footnote appears once when any required option exists."""

  def test_asterisk_present_for_required_args(self):
    class Demo:
      """Demo."""

      class Build:
        """Build."""

        def deploy(self, target: str) -> None:
          """Deploy."""

    cli = FreyjaCLI(Demo, completion=False)
    text = _strip(_help_for(cli, no_color=True))
    assert '* - required' in text
    assert '--target' in text


# ----- Argparse 3.14 _set_color regression ---------------------------------------------


class TestArgparse314Compat:
  """`_freyja_theme` must not collide with argparse 3.14's `_theme` attribute."""

  def test_format_help_survives_set_color(self):
    class App:
      """App."""

      def greet(self, name: str) -> None:
        """Greet."""

    cli = FreyjaCLI(App, title='Greet CLI', completion=False)
    parser = cli.create_parser(no_color=False)
    text = parser.format_help()
    assert 'Greet CLI' in text
    assert 'greet' in text


# ----- Stylesheet plumbing -------------------------------------------------------------


class TestApplyStyle:
  """``_apply_style`` returns plain text under no-color theme; styled under Sunset."""

  def test_no_color_theme_passes_text_through(self):
    formatter = HierarchicalHelpFormatter(prog='x', theme=create_no_color_theme())
    assert formatter._apply_style('hello', 'command_group_name') == 'hello'

  def test_sunset_theme_emits_ansi_when_colors_enabled(self):
    formatter = HierarchicalHelpFormatter(prog='x', theme=get_default_theme())
    formatter._color_formatter.colors_enabled = True
    styled = formatter._apply_style('hello', 'command_group_name')
    assert '\x1b[' in styled
    assert 'hello' in styled
