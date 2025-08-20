from typing import Tuple, Union


class MathUtils:
  EPSILON: float = 1e-6
  Numeric = Union[int, float]

  @classmethod
  def clamp(cls, value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max bounds and return it.
      :value: The value to clamp
      :min_val: Minimum allowed value
      :max_val: Maximum allowed value
    """
    return max(min_val, min(value, max_val))

  @classmethod
  def minmax_range(cls, *args: Numeric, negative_lower: bool = False) -> Tuple[Numeric, Numeric]:
    mm = cls.minmax(*args)
    return -mm[0] if negative_lower else mm[0], mm[1]

  @classmethod
  def minmax(cls, *args: Numeric) -> Tuple[Numeric, Numeric]:
    """
    Return the minimum and maximum of a dynamic number of arguments.
      :args: Variable number of int or float arguments

    Raises:
        ValueError: If no arguments are provided
    """
    if not args: raise ValueError("minmax() requires at least one argument")

    return min(args), max(args)

  @classmethod
  def percent(cls, val: int | float, max_val: int | float) -> float:
    if max_val < cls.EPSILON: raise ValueError("max_val is too small")
    return (max_val - val) / float(max_val)
