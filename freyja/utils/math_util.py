from typing import Union


class MathUtil:
  EPSILON: float = 1e-6
  Numeric = Union[int, float]

  @classmethod
  def clamp(cls, value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max bounds and return it.
      :value: The value to clamp
      :min_val: Minimum allowed value
      :max_val: Maximum allowed value

    Examples:
        MathUtil.clamp(5, 0, 10) # 5
        MathUtil.clamp(-5, 0, 10) # 0
        MathUtil.clamp(15, 0, 10) # 10
    """
    return max(min_val, min(value, max_val))

  @classmethod
  def minmax_range(cls, args: [Numeric], negative_lower: bool = False) -> tuple[Numeric, Numeric]:
    lower, upper = cls.minmax(*args)

    return cls.safe_negative(lower, negative_lower), upper

  @classmethod
  def minmax(cls, *args: Numeric) -> tuple[Numeric, Numeric]:
    """
    Return the minimum and maximum of a dynamic number of arguments.
      :args: Variable number of int or float arguments

    Raises:
        ValueError: If no arguments are provided
    """
    if not args:
      raise ValueError("minmax() requires at least one argument")

    return min(args), max(args)

  @classmethod
  def safe_negative(cls, value: Numeric, neg: bool = True) -> Numeric:
    """
    Return the negative of a dynamic number only if neg is True.
    :param value: Value to check and convert
    :param neg: Whether to convert to negative or not
    """
    return -value if neg else value

  @classmethod
  def percent(cls, val: int | float, max_val: int | float) -> float:
    if max_val < cls.EPSILON: raise ValueError("max_val is too small")
    return val / float(max_val)
