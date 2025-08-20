"""Tests for color adjustment functionality in themes."""
import pytest

from auto_cli.math_utils import MathUtils
from auto_cli.theme import (
  AdjustStrategy,
  Themes,
  ThemeStyle,
  create_default_theme,
  hex_to_rgb,
  rgb_to_hex,
  is_valid_hex_color
)


class TestColorUtils:
    """Test utility functions for color manipulation."""

    def test_hex_to_rgb(self):
        """Test hex to RGB conversion."""
        assert hex_to_rgb("#FF0000") == (255, 0, 0)
        assert hex_to_rgb("#00FF00") == (0, 255, 0)
        assert hex_to_rgb("#0000FF") == (0, 0, 255)
        assert hex_to_rgb("#FFFFFF") == (255, 255, 255)
        assert hex_to_rgb("#000000") == (0, 0, 0)
        assert hex_to_rgb("808080") == (128, 128, 128)  # No # prefix

    def test_rgb_to_hex(self):
        """Test RGB to hex conversion."""
        assert rgb_to_hex(255, 0, 0) == "#ff0000"
        assert rgb_to_hex(0, 255, 0) == "#00ff00"
        assert rgb_to_hex(0, 0, 255) == "#0000ff"
        assert rgb_to_hex(255, 255, 255) == "#ffffff"
        assert rgb_to_hex(0, 0, 0) == "#000000"
        assert rgb_to_hex(128, 128, 128) == "#808080"

    def test_clamp(self):
        """Test clamping function."""
        assert MathUtils.clamp(50, 0, 100) == 50
        assert MathUtils.clamp(-10, 0, 100) == 0
        assert MathUtils.clamp(150, 0, 100) == 100
        assert MathUtils.clamp(255, 0, 255) == 255
        assert MathUtils.clamp(300, 0, 255) == 255

    def test_is_valid_hex_color(self):
        """Test hex color validation."""
        assert is_valid_hex_color("#FF0000") is True
        assert is_valid_hex_color("FF0000") is True
        assert is_valid_hex_color("#ffffff") is True
        assert is_valid_hex_color("#XYZ123") is False
        assert is_valid_hex_color("invalid") is False
        assert is_valid_hex_color("#FF00") is False  # Too short
        assert is_valid_hex_color("#FF000000") is False  # Too long

    def test_hex_to_rgb_invalid(self):
        """Test hex to RGB with invalid inputs."""
        with pytest.raises(ValueError):
            hex_to_rgb("invalid")

        with pytest.raises(ValueError):
            hex_to_rgb("#XYZ123")

        with pytest.raises(ValueError):
            hex_to_rgb("#FF00")  # Too short


class TestAdjustStrategy:
    """Test the AdjustStrategy enum."""

    def test_enum_values(self):
        """Test enum has correct values."""
        assert AdjustStrategy.PROPORTIONAL.value == "proportional"
        assert AdjustStrategy.ABSOLUTE.value == "absolute"


class TestThemeColorAdjustment:
    """Test color adjustment functionality in themes."""

    def test_theme_creation_with_adjustment(self):
        """Test creating theme with adjustment parameters."""
        theme = create_default_theme()
        theme.adjust_percent = 0.3
        theme.adjust_strategy = AdjustStrategy.PROPORTIONAL

        assert theme.adjust_percent == 0.3
        assert theme.adjust_strategy == AdjustStrategy.PROPORTIONAL

    def test_proportional_adjustment_positive(self):
        """Test proportional color adjustment with positive percentage."""
        style = ThemeStyle(fg="#808080")  # Mid gray (128, 128, 128)
        theme = Themes(
            title=style, subtitle=style, command_name=style, command_description=style,
            group_command_name=style, subcommand_name=style, subcommand_description=style,
            option_name=style, option_description=style, required_option_name=style,
            required_option_description=style, required_asterisk=style,
            adjust_strategy=AdjustStrategy.PROPORTIONAL,
            adjust_percent=0.25  # 25% brighter
        )

        adjusted_color = theme.adjust_color("#808080")
        r, g, b = hex_to_rgb(adjusted_color)

        # Each component should be increased by 25%: 128 + (128 * 0.25) = 160
        assert r == 160
        assert g == 160
        assert b == 160

    def test_proportional_adjustment_negative(self):
        """Test proportional color adjustment with negative percentage."""
        style = ThemeStyle(fg="#808080")  # Mid gray (128, 128, 128)
        theme = Themes(
            title=style, subtitle=style, command_name=style, command_description=style,
            group_command_name=style, subcommand_name=style, subcommand_description=style,
            option_name=style, option_description=style, required_option_name=style,
            required_option_description=style, required_asterisk=style,
            adjust_strategy=AdjustStrategy.PROPORTIONAL,
            adjust_percent=-0.25  # 25% darker
        )

        adjusted_color = theme.adjust_color("#808080")
        r, g, b = hex_to_rgb(adjusted_color)

        # Each component should be decreased by 25%: 128 + (128 * -0.25) = 96
        assert r == 96
        assert g == 96
        assert b == 96

    def test_absolute_adjustment_positive(self):
        """Test absolute color adjustment with positive percentage."""
        style = ThemeStyle(fg="#404040")  # Dark gray (64, 64, 64)
        theme = Themes(
            title=style, subtitle=style, command_name=style, command_description=style,
            group_command_name=style, subcommand_name=style, subcommand_description=style,
            option_name=style, option_description=style, required_option_name=style,
            required_option_description=style, required_asterisk=style,
            adjust_strategy=AdjustStrategy.ABSOLUTE,
            adjust_percent=0.5  # 50% increase
        )

        adjusted_color = theme.adjust_color("#404040")
        r, g, b = hex_to_rgb(adjusted_color)

        # Each component should be increased by 50%: 64 + (64 * 0.5) = 96
        assert r == 96
        assert g == 96
        assert b == 96

    def test_absolute_adjustment_with_clamping(self):
        """Test absolute adjustment with clamping at boundaries."""
        style = ThemeStyle(fg="#F0F0F0")  # Light gray (240, 240, 240)
        theme = Themes(
            title=style, subtitle=style, command_name=style, command_description=style,
            group_command_name=style, subcommand_name=style, subcommand_description=style,
            option_name=style, option_description=style, required_option_name=style,
            required_option_description=style, required_asterisk=style,
            adjust_strategy=AdjustStrategy.ABSOLUTE,
            adjust_percent=0.5  # 50% increase would exceed 255
        )

        adjusted_color = theme.adjust_color("#F0F0F0")
        r, g, b = hex_to_rgb(adjusted_color)

        # Should clamp at 255: 240 + (240 * 0.5) = 360, clamped to 255
        assert r == 255
        assert g == 255
        assert b == 255

    def test_safe_adjustment_calculation(self):
        """Test proportional safe adjustment calculation."""
        style = ThemeStyle(fg="#E0E0E0")  # Light gray (224, 224, 224)
        theme = Themes(
            title=style, subtitle=style, command_name=style, command_description=style,
            group_command_name=style, subcommand_name=style, subcommand_description=style,
            option_name=style, option_description=style, required_option_name=style,
            required_option_description=style, required_asterisk=style,
            adjust_strategy=AdjustStrategy.PROPORTIONAL,
            adjust_percent=0.5  # 50% would overflow, should be limited
        )

        safe_adj = theme.max_rgb_adjust(224, 224, 224)

        # Maximum safe adjustment: (255-224)/224 ≈ 0.138
        # Should be less than requested 0.5
        assert safe_adj < 0.5
        assert safe_adj > 0

    def test_get_adjusted_style(self):
        """Test getting adjusted style by name."""
        original_style = ThemeStyle(fg="#808080", bold=True, italic=False)
        theme = Themes(
            title=original_style, subtitle=original_style, command_name=original_style,
            command_description=original_style, group_command_name=original_style,
            subcommand_name=original_style, subcommand_description=original_style,
            option_name=original_style, option_description=original_style,
            required_option_name=original_style, required_option_description=original_style,
            required_asterisk=original_style,
            adjust_strategy=AdjustStrategy.PROPORTIONAL,
            adjust_percent=0.25
        )

        adjusted_style = theme.get_adjusted_style('title')

        assert adjusted_style is not None
        assert adjusted_style.fg != "#808080"  # Should be adjusted
        assert adjusted_style.bold is True  # Non-color properties preserved
        assert adjusted_style.italic is False

    def test_adjustment_with_non_hex_colors(self):
        """Test adjustment ignores non-hex colors."""
        style = ThemeStyle(fg="\x1b[31m")  # ANSI code, should not be adjusted
        theme = Themes(
            title=style, subtitle=style, command_name=style, command_description=style,
            group_command_name=style, subcommand_name=style, subcommand_description=style,
            option_name=style, option_description=style, required_option_name=style,
            required_option_description=style, required_asterisk=style,
            adjust_strategy=AdjustStrategy.PROPORTIONAL,
            adjust_percent=0.25
        )

        adjusted_color = theme.adjust_color("\x1b[31m")

        # Should return unchanged
        assert adjusted_color == "\x1b[31m"

    def test_adjustment_with_zero_percent(self):
        """Test no adjustment when percent is 0."""
        style = ThemeStyle(fg="#FF0000")
        theme = Themes(
            title=style, subtitle=style, command_name=style, command_description=style,
            group_command_name=style, subcommand_name=style, subcommand_description=style,
            option_name=style, option_description=style, required_option_name=style,
            required_option_description=style, required_asterisk=style,
            adjust_percent=0.0  # No adjustment
        )

        adjusted_color = theme.adjust_color("#FF0000")

        assert adjusted_color == "#FF0000"

    def test_create_adjusted_copy(self):
        """Test creating an adjusted copy of a theme."""
        original_theme = create_default_theme()
        adjusted_theme = original_theme.create_adjusted_copy(0.2)

        assert adjusted_theme.adjust_percent == 0.2
        assert adjusted_theme != original_theme  # Different instances

        # Original theme should be unchanged
        assert original_theme.adjust_percent == 0.0

    def test_adjustment_edge_cases(self):
        """Test adjustment with edge case colors."""
        theme = Themes(
            title=ThemeStyle(), subtitle=ThemeStyle(), command_name=ThemeStyle(),
            command_description=ThemeStyle(), group_command_name=ThemeStyle(),
            subcommand_name=ThemeStyle(), subcommand_description=ThemeStyle(),
            option_name=ThemeStyle(), option_description=ThemeStyle(),
            required_option_name=ThemeStyle(), required_option_description=ThemeStyle(),
            required_asterisk=ThemeStyle(),
            adjust_strategy=AdjustStrategy.PROPORTIONAL,
            adjust_percent=0.5
        )

        # Test with black (should handle division by zero)
        adjusted_black = theme.adjust_color("#000000")
        assert adjusted_black == "#000000"  # Can't adjust pure black

        # Test with white
        adjusted_white = theme.adjust_color("#FFFFFF")
        assert adjusted_white == "#ffffff"  # Can't brighten pure white

        # Test with None
        adjusted_none = theme.adjust_color(None)
        assert adjusted_none is None

    def test_adjust_percent_validation_in_init(self):
        """Test adjust_percent validation in Themes.__init__."""
        style = ThemeStyle()

        # Valid range should work
        Themes(
            title=style, subtitle=style, command_name=style, command_description=style,
            group_command_name=style, subcommand_name=style, subcommand_description=style,
            option_name=style, option_description=style, required_option_name=style,
            required_option_description=style, required_asterisk=style,
            adjust_percent=-5.0  # Minimum valid
        )

        Themes(
            title=style, subtitle=style, command_name=style, command_description=style,
            group_command_name=style, subcommand_name=style, subcommand_description=style,
            option_name=style, option_description=style, required_option_name=style,
            required_option_description=style, required_asterisk=style,
            adjust_percent=5.0  # Maximum valid
        )

        # Below minimum should raise exception
        with pytest.raises(ValueError, match="adjust_percent must be between -5.0 and 5.0, got -5.1"):
            Themes(
                title=style, subtitle=style, command_name=style, command_description=style,
                group_command_name=style, subcommand_name=style, subcommand_description=style,
                option_name=style, option_description=style, required_option_name=style,
                required_option_description=style, required_asterisk=style,
                adjust_percent=-5.1
            )

        # Above maximum should raise exception
        with pytest.raises(ValueError, match="adjust_percent must be between -5.0 and 5.0, got 5.1"):
            Themes(
                title=style, subtitle=style, command_name=style, command_description=style,
                group_command_name=style, subcommand_name=style, subcommand_description=style,
                option_name=style, option_description=style, required_option_name=style,
                required_option_description=style, required_asterisk=style,
                adjust_percent=5.1
            )

    def test_adjust_percent_validation_in_create_adjusted_copy(self):
        """Test adjust_percent validation in create_adjusted_copy method."""
        original_theme = create_default_theme()

        # Valid range should work
        original_theme.create_adjusted_copy(-5.0)  # Minimum valid
        original_theme.create_adjusted_copy(5.0)   # Maximum valid

        # Below minimum should raise exception
        with pytest.raises(ValueError, match="adjust_percent must be between -5.0 and 5.0, got -5.1"):
            original_theme.create_adjusted_copy(-5.1)

        # Above maximum should raise exception
        with pytest.raises(ValueError, match="adjust_percent must be between -5.0 and 5.0, got 5.1"):
            original_theme.create_adjusted_copy(5.1)
