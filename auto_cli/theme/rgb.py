"""Immutable RGB color class with comprehensive color operations."""
from __future__ import annotations

from enum import Enum
from typing import Tuple
import colorsys

from auto_cli.math_utils import MathUtils


class AdjustStrategy(Enum):
    """Strategy for color adjustment calculations."""
    PROPORTIONAL = "proportional"  # Scales adjustment based on color intensity
    ABSOLUTE = "absolute"  # Direct percentage adjustment with clamping
    RELATIVE = "relative"  # Relative adjustment (legacy compatibility)


class RGB:
    """Immutable RGB color representation with values in range 0.0-1.0."""

    def __init__(self, r: float, g: float, b: float):
        """Initialize RGB with float values 0.0-1.0.

        :param r: Red component (0.0-1.0)
        :param g: Green component (0.0-1.0)
        :param b: Blue component (0.0-1.0)
        :raises ValueError: If any value is outside 0.0-1.0 range
        """
        if not (0.0 <= r <= 1.0):
            raise ValueError(f"Red component must be between 0.0 and 1.0, got {r}")
        if not (0.0 <= g <= 1.0):
            raise ValueError(f"Green component must be between 0.0 and 1.0, got {g}")
        if not (0.0 <= b <= 1.0):
            raise ValueError(f"Blue component must be between 0.0 and 1.0, got {b}")

        self._r = r
        self._g = g
        self._b = b

    @property
    def r(self) -> float:
        """Red component (0.0-1.0)."""
        return self._r

    @property
    def g(self) -> float:
        """Green component (0.0-1.0)."""
        return self._g

    @property
    def b(self) -> float:
        """Blue component (0.0-1.0)."""
        return self._b

    @classmethod
    def from_ints(cls, r: int, g: int, b: int) -> 'RGB':
        """Create RGB from integer values 0-255.

        :param r: Red component (0-255)
        :param g: Green component (0-255)
        :param b: Blue component (0-255)
        :return: RGB instance
        :raises ValueError: If any value is outside 0-255 range
        """
        if not (0 <= r <= 255):
            raise ValueError(f"Red component must be between 0 and 255, got {r}")
        if not (0 <= g <= 255):
            raise ValueError(f"Green component must be between 0 and 255, got {g}")
        if not (0 <= b <= 255):
            raise ValueError(f"Blue component must be between 0 and 255, got {b}")

        return cls(r / 255.0, g / 255.0, b / 255.0)

    @classmethod
    def from_rgb(cls, rgb: int) -> 'RGB':
        """Create RGB from hex integer (0x000000 to 0xFFFFFF).

        :param rgb: RGB value as integer (0x000000 to 0xFFFFFF)
        :return: RGB instance
        :raises ValueError: If value is outside valid range
        """
        if not (0 <= rgb <= 0xFFFFFF):
            raise ValueError(f"RGB value must be between 0 and 0xFFFFFF, got {rgb:06X}")

        # Extract RGB components from hex number
        r = (rgb >> 16) & 0xFF
        g = (rgb >> 8) & 0xFF
        b = rgb & 0xFF

        return cls.from_ints(r, g, b)


    def to_hex(self) -> str:
        """Convert to hex string format '#RRGGBB'.

        :return: Hex color string (e.g., '#FF5733')
        """
        r = int(self._r * 255)
        g = int(self._g * 255)
        b = int(self._b * 255)
        return f"#{r:02X}{g:02X}{b:02X}"

    def to_ints(self) -> Tuple[int, int, int]:
        """Convert to integer RGB tuple (0-255 range).

        :return: RGB tuple with integer values
        """
        return (
            int(self._r * 255),
            int(self._g * 255),
            int(self._b * 255)
        )

    def to_ansi(self, background: bool = False) -> str:
        """Convert to ANSI escape code.

        :param background: Whether this is a background color
        :return: ANSI color code string
        """
        # Convert to 0-255 range
        r, g, b = self.to_ints()

        # Find closest ANSI 256 color
        ansi_code = self._rgb_to_ansi256(r, g, b)

        # Return appropriate ANSI escape sequence
        prefix = '\033[48;5;' if background else '\033[38;5;'
        return f"{prefix}{ansi_code}m"

    def adjust(self, *, brightness: float = 0.0, saturation: float = 0.0,
               strategy: AdjustStrategy = AdjustStrategy.RELATIVE) -> 'RGB':
        """Adjust color brightness and/or saturation, returning new RGB instance.

        :param brightness: Brightness adjustment (-5.0 to 5.0)
        :param saturation: Saturation adjustment (-5.0 to 5.0)
        :param strategy: Adjustment strategy
        :return: New RGB instance with adjustments applied
        :raises ValueError: If adjustment values are out of range
        """
        if not (-5.0 <= brightness <= 5.0):
            raise ValueError(f"Brightness must be between -5.0 and 5.0, got {brightness}")
        if not (-5.0 <= saturation <= 5.0):
            raise ValueError(f"Saturation must be between -5.0 and 5.0, got {saturation}")

        # If no adjustments, return self (immutable)
        if brightness == 0.0 and saturation == 0.0:
            return self

        # Convert to integer for adjustment algorithm (matches existing behavior)
        r, g, b = self.to_ints()

        # Apply brightness adjustment (using existing algorithm from themes.py)
        # NOTE: The original algorithm has a bug where positive brightness makes colors darker
        # We maintain this behavior for backward compatibility
        if brightness != 0.0:
            factor = -brightness
            if brightness >= 0:
                # Original buggy behavior: negative factor makes colors darker
                r, g, b = [int(v + (255 - v) * factor) for v in (r, g, b)]
            else:
                # Darker - blend with black (0, 0, 0)
                factor = 1 + brightness  # brightness is negative, so this reduces values
                r, g, b = [int(v * factor) for v in (r, g, b)]

        # Clamp to valid range
        r, g, b = [int(MathUtils.clamp(v, 0, 255)) for v in (r, g, b)]

        # TODO: Add saturation adjustment when needed
        # For now, just brightness adjustment to match existing behavior

        return RGB.from_ints(r, g, b)

    def _rgb_to_ansi256(self, r: int, g: int, b: int) -> int:
        """Convert RGB values to the closest ANSI 256-color code.

        :param r: Red component (0-255)
        :param g: Green component (0-255)
        :param b: Blue component (0-255)
        :return: ANSI color code (0-255)
        """
        # Check if it's close to grayscale (colors 232-255)
        if abs(r - g) < 10 and abs(g - b) < 10 and abs(r - b) < 10:
            # Use grayscale palette (24 shades)
            gray = (r + g + b) // 3
            if gray < 8:
                return 16  # Black
            elif gray > 238:
                return 231  # White
            else:
                return 232 + (gray - 8) * 23 // 230

        # Use 6x6x6 color cube (colors 16-231)
        # Map RGB values to 6-level scale (0-5)
        r6 = min(5, r * 6 // 256)
        g6 = min(5, g * 6 // 256)
        b6 = min(5, b * 6 // 256)

        return 16 + (36 * r6) + (6 * g6) + b6

    def __eq__(self, other) -> bool:
        """Check equality with another RGB instance."""
        return (isinstance(other, RGB) and
                self._r == other._r and
                self._g == other._g and
                self._b == other._b)

    def __hash__(self) -> int:
        """Make RGB hashable."""
        return hash((self._r, self._g, self._b))

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"RGB(r={self._r:.3f}, g={self._g:.3f}, b={self._b:.3f})"

    def __str__(self) -> str:
        """User-friendly string representation."""
        return self.to_hex()
