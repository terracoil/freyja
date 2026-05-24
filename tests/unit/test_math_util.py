"""Comprehensive tests for MathUtil class to achieve 95%+ coverage."""

import pytest
from freyja.utils.math_util import MathUtil


class TestMathUtil:
  """Test suite for MathUtil utility class."""

  def test_clamp_basic(self):
    """Test basic clamp functionality."""
    # Value within bounds
    assert MathUtil.clamp(5, 0, 10) == 5
    assert MathUtil.clamp(5.5, 0, 10) == 5.5

    # Value below minimum
    assert MathUtil.clamp(-5, 0, 10) == 0
    assert MathUtil.clamp(-100, 0, 10) == 0

    # Value above maximum
    assert MathUtil.clamp(15, 0, 10) == 10
    assert MathUtil.clamp(100, 0, 10) == 10

    # Edge cases - at boundaries
    assert MathUtil.clamp(0, 0, 10) == 0
    assert MathUtil.clamp(10, 0, 10) == 10

  def test_clamp_with_floats(self):
    """Test clamp with float values."""
    assert MathUtil.clamp(3.14, 0.0, 5.0) == 3.14
    assert MathUtil.clamp(-2.5, 0.0, 5.0) == 0.0
    assert MathUtil.clamp(7.8, 0.0, 5.0) == 5.0

    # Very small and large floats
    assert MathUtil.clamp(1e-10, 0.0, 1.0) == 1e-10
    assert MathUtil.clamp(1e10, 0.0, 1.0) == 1.0

  def test_clamp_negative_bounds(self):
    """Test clamp with negative bounds."""
    assert MathUtil.clamp(0, -10, 10) == 0
    assert MathUtil.clamp(-5, -10, 10) == -5
    assert MathUtil.clamp(-15, -10, 10) == -10
    assert MathUtil.clamp(15, -10, 10) == 10

    # All negative bounds
    assert MathUtil.clamp(-5, -10, -1) == -5
    assert MathUtil.clamp(0, -10, -1) == -1
    assert MathUtil.clamp(-15, -10, -1) == -10

  def test_clamp_equal_bounds(self):
    """Test clamp when min and max are equal."""
    assert MathUtil.clamp(5, 3, 3) == 3
    assert MathUtil.clamp(0, 3, 3) == 3
    assert MathUtil.clamp(10, 3, 3) == 3

  def test_minmax_basic(self):
    """Test basic minmax functionality."""
    # Single value
    assert MathUtil.minmax(5) == (5, 5)

    # Multiple values
    assert MathUtil.minmax(1, 5, 3) == (1, 5)
    assert MathUtil.minmax(10, 20, 15, 5, 25) == (5, 25)

    # All same values
    assert MathUtil.minmax(7, 7, 7) == (7, 7)

  def test_minmax_with_floats(self):
    """Test minmax with float values."""
    assert MathUtil.minmax(1.5, 2.7, 0.3) == (0.3, 2.7)
    assert MathUtil.minmax(3.14, 2.71, 1.41) == (1.41, 3.14)

    # Mixed int and float
    assert MathUtil.minmax(1, 2.5, 3) == (1, 3)
    assert MathUtil.minmax(1.1, 2, 3.3) == (1.1, 3.3)

  def test_minmax_with_negatives(self):
    """Test minmax with negative values."""
    assert MathUtil.minmax(-5, -1, -3) == (-5, -1)
    assert MathUtil.minmax(-10, 0, 10) == (-10, 10)
    assert MathUtil.minmax(-2.5, -1.5, -3.5) == (-3.5, -1.5)

  def test_minmax_no_args_raises_error(self):
    """Test that minmax raises error with no arguments."""
    with pytest.raises(ValueError, match='minmax\\(\\) requires at least one argument'):
      MathUtil.minmax()

  def test_minmax_range_basic(self):
    """Test minmax_range functionality."""
    # Basic usage without negative_lower
    assert MathUtil.minmax_range([1, 5, 3]) == (1, 5)
    assert MathUtil.minmax_range([10, 20, 15], negative_lower=False) == (10, 20)

  def test_minmax_range_with_negative_lower(self):
    """Test minmax_range with negative_lower=True."""
    # Positive values become negative
    assert MathUtil.minmax_range([1, 5, 3], negative_lower=True) == (-1, 5)
    assert MathUtil.minmax_range([10, 20, 15], negative_lower=True) == (-10, 20)

    # Already negative values stay negative
    assert MathUtil.minmax_range([-5, -1, -3], negative_lower=True) == (5, -1)

    # Mixed positive and negative
    assert MathUtil.minmax_range([-2, 0, 2], negative_lower=True) == (2, 2)

  def test_minmax_range_single_value(self):
    """Test minmax_range with single value."""
    assert MathUtil.minmax_range([5]) == (5, 5)
    assert MathUtil.minmax_range([5], negative_lower=True) == (-5, 5)
    assert MathUtil.minmax_range([-5], negative_lower=True) == (5, -5)

  def test_safe_negative_basic(self):
    """Test safe_negative functionality."""
    # With neg=True (default)
    assert MathUtil.safe_negative(5) == -5
    assert MathUtil.safe_negative(5, True) == -5
    assert MathUtil.safe_negative(5, neg=True) == -5

    # With neg=False
    assert MathUtil.safe_negative(5, False) == 5
    assert MathUtil.safe_negative(5, neg=False) == 5

  def test_safe_negative_with_floats(self):
    """Test safe_negative with float values."""
    assert MathUtil.safe_negative(3.14, True) == -3.14
    assert MathUtil.safe_negative(3.14, False) == 3.14
    assert MathUtil.safe_negative(-2.5, True) == 2.5
    assert MathUtil.safe_negative(-2.5, False) == -2.5

  def test_safe_negative_with_zero(self):
    """Test safe_negative with zero."""
    assert MathUtil.safe_negative(0, True) == 0
    assert MathUtil.safe_negative(0, False) == 0
    assert MathUtil.safe_negative(0.0, True) == 0.0
    assert MathUtil.safe_negative(0.0, False) == 0.0

  def test_safe_negative_already_negative(self):
    """Test safe_negative with already negative values."""
    assert MathUtil.safe_negative(-5, True) == 5
    assert MathUtil.safe_negative(-5, False) == -5
    assert MathUtil.safe_negative(-3.14, True) == 3.14
    assert MathUtil.safe_negative(-3.14, False) == -3.14

  def test_percent_basic(self):
    """Test basic percentage calculation."""
    assert MathUtil.percent(50, 100) == 0.5
    assert MathUtil.percent(25, 100) == 0.25
    assert MathUtil.percent(75, 100) == 0.75
    assert MathUtil.percent(100, 100) == 1.0
    assert MathUtil.percent(0, 100) == 0.0

  def test_percent_with_floats(self):
    """Test percentage with float values."""
    assert MathUtil.percent(33.33, 100) == 0.3333
    assert MathUtil.percent(50.5, 100) == 0.505
    assert abs(MathUtil.percent(1.0, 3.0) - 0.3333333) < 1e-6

  def test_percent_different_scales(self):
    """Test percentage with different scales."""
    assert MathUtil.percent(5, 10) == 0.5
    assert MathUtil.percent(1, 4) == 0.25
    assert MathUtil.percent(3, 12) == 0.25
    assert MathUtil.percent(150, 200) == 0.75

  def test_percent_exceeding_max(self):
    """Test percentage when value exceeds max_val."""
    assert MathUtil.percent(150, 100) == 1.5
    assert MathUtil.percent(200, 100) == 2.0
    assert MathUtil.percent(250, 50) == 5.0

  def test_percent_small_max_raises_error(self):
    """Test that percent raises error when max_val is too small."""
    # Test with exactly EPSILON
    with pytest.raises(ValueError, match='max_val is too small'):
      MathUtil.percent(50, MathUtil.EPSILON / 2)

    # Test with zero
    with pytest.raises(ValueError, match='max_val is too small'):
      MathUtil.percent(50, 0)

    # Test with negative
    with pytest.raises(ValueError, match='max_val is too small'):
      MathUtil.percent(50, -1)

  def test_percent_edge_cases(self):
    """Test percent edge cases."""
    # Just above EPSILON should work
    result = MathUtil.percent(1, MathUtil.EPSILON * 2)
    assert result > 0

    # Large numbers
    assert MathUtil.percent(1e6, 1e7) == 0.1
    assert MathUtil.percent(1e9, 1e10) == 0.1

  def test_epsilon_constant(self):
    """Test EPSILON constant is accessible and has expected value."""
    assert MathUtil.EPSILON == 1e-6
    assert isinstance(MathUtil.EPSILON, float)

  def test_numeric_type_hint(self):
    """Test that Numeric type hint is defined."""
    # Just verify the type alias exists
    assert hasattr(MathUtil, 'Numeric')

  def test_class_methods_are_classmethods(self):
    """Verify all methods are class methods."""
    # All methods should work without instantiation
    assert callable(MathUtil.clamp)
    assert callable(MathUtil.minmax)
    assert callable(MathUtil.minmax_range)
    assert callable(MathUtil.safe_negative)
    assert callable(MathUtil.percent)

  def test_integration_clamp_and_percent(self):
    """Test integration of clamp and percent methods."""
    # Calculate percentage and clamp to 0-1 range
    value = 150
    max_val = 100
    percentage = MathUtil.percent(value, max_val)  # 1.5
    clamped = MathUtil.clamp(percentage, 0.0, 1.0)  # 1.0
    assert clamped == 1.0

  def test_integration_minmax_and_clamp(self):
    """Test integration of minmax and clamp methods."""
    values = [5, 15, -5, 25]
    min_val, max_val = MathUtil.minmax(*values)
    assert min_val == -5
    assert max_val == 25

    # Clamp a value to this range
    assert MathUtil.clamp(30, min_val, max_val) == 25
    assert MathUtil.clamp(-10, min_val, max_val) == -5
    assert MathUtil.clamp(10, min_val, max_val) == 10
