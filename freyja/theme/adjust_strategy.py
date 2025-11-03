"""Strategy for color adjustment calculations."""

from enum import Enum


class AdjustStrategy(Enum):
  """Strategy for color adjustment calculations."""

  LINEAR = "linear"
  COLOR_HSL = "color_hsl"
  MULTIPLICATIVE = "multiplicative"
  GAMMA = "gamma"
  LUMINANCE = "luminance"
  OVERLAY = "overlay"
  ABSOLUTE = "absolute"  # Legacy absolute adjustment