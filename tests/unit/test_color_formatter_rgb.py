"""Tests for ColorFormatter applying ThemeStyle to text via ANSI escapes."""

from freyja.theme import RGB, ColorFormatter, ThemeStyle


class TestColorFormatter256:
  """Force 256-color mode for predictable ANSI output regardless of $COLORTERM."""

  def _formatter(self) -> ColorFormatter:
    return ColorFormatter(enable_colors=True, truecolor=False)

  def test_apply_style_with_rgb_foreground(self):
    style = ThemeStyle(fg=RGB.from_rgb(0xFF5733))
    result = self._formatter().apply_style('test', style)
    assert '\x1b[38;5;' in result
    assert 'test' in result
    assert '\x1b[0m' in result

  def test_apply_style_with_rgb_background(self):
    style = ThemeStyle(bg=RGB.from_rgb(0x00FF00))
    result = self._formatter().apply_style('test', style)
    assert '\x1b[48;5;' in result
    assert 'test' in result

  def test_apply_style_with_rgb_both_colors_and_bold(self):
    style = ThemeStyle(fg=RGB.from_rgb(0xFF5733), bg=RGB.from_rgb(0x00FF00), bold=True)
    result = self._formatter().apply_style('test', style)
    assert '\x1b[38;5;' in result
    assert '\x1b[48;5;' in result
    assert '\x1b[1m' in result
    assert '\x1b[0m' in result

  def test_apply_style_rgb_consistency(self):
    formatter = self._formatter()
    rgb_a = RGB.from_rgb(0xFF5733)
    r, g, b = rgb_a.to_ints()
    rgb_b = RGB.from_ints(r, g, b)
    assert formatter.apply_style('x', ThemeStyle(fg=rgb_a)) == formatter.apply_style(
      'x', ThemeStyle(fg=rgb_b)
    )

  def test_all_text_decorations(self):
    style = ThemeStyle(fg=RGB.from_rgb(0xFF5733), bold=True, italic=True, dim=True, underline=True)
    result = self._formatter().apply_style('test', style)
    for code in ('\x1b[38;5;', '\x1b[1m', '\x1b[3m', '\x1b[2m', '\x1b[4m', '\x1b[0m'):
      assert code in result


class TestColorFormatterTruecolor:
  """24-bit emission when truecolor mode is enabled."""

  def _formatter(self) -> ColorFormatter:
    return ColorFormatter(enable_colors=True, truecolor=True)

  def test_truecolor_foreground(self):
    style = ThemeStyle(fg=RGB.from_rgb(0xCB4B16))
    result = self._formatter().apply_style('test', style)
    assert '\x1b[38;2;203;75;22m' in result
    assert '\x1b[0m' in result

  def test_truecolor_background(self):
    style = ThemeStyle(bg=RGB.from_rgb(0xCB4B16))
    result = self._formatter().apply_style('test', style)
    assert '\x1b[48;2;203;75;22m' in result


class TestColorFormatterDisabled:
  """When COLORS are disabled, text passes through untouched."""

  def test_colors_disabled_returns_plain(self):
    formatter = ColorFormatter(enable_colors=False)
    style = ThemeStyle(fg=RGB.from_rgb(0xFF5733), bold=True)
    assert formatter.apply_style('test', style) == 'test'

  def test_empty_text_returns_empty(self):
    formatter = ColorFormatter(enable_colors=True, truecolor=False)
    assert formatter.apply_style('', ThemeStyle(fg=RGB.from_rgb(0xFF5733))) == ''

  def test_none_text_returns_none(self):
    formatter = ColorFormatter(enable_colors=True, truecolor=False)
    assert formatter.apply_style(None, ThemeStyle(fg=RGB.from_rgb(0xFF5733))) is None
