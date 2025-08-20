class MathUtils:
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp a value between min and max bounds.

        Args:
            value: The value to clamp
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            The clamped value

        Examples:
            >>> MathUtils.clamp(5, 0, 10)
            5
            >>> MathUtils.clamp(-5, 0, 10)
            0
            >>> MathUtils.clamp(15, 0, 10)
            10
        """
        return max(min_val, min(value, max_val))