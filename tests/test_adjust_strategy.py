"""Tests for AdjustStrategy enum."""

from auto_cli.theme import AdjustStrategy


class TestAdjustStrategy:
    """Test the AdjustStrategy enum."""

    def test_enum_values(self):
        """Test enum has correct values."""
        assert AdjustStrategy.PROPORTIONAL.value == "proportional"
        assert AdjustStrategy.ABSOLUTE.value == "absolute"

    def test_enum_members(self):
        """Test enum has all expected members."""
        expected_members = {'PROPORTIONAL', 'ABSOLUTE', 'RELATIVE'}
        actual_members = {member.name for member in AdjustStrategy}
        assert expected_members.issubset(actual_members)

    def test_enum_string_representation(self):
        """Test enum string representations."""
        assert str(AdjustStrategy.PROPORTIONAL) == "AdjustStrategy.PROPORTIONAL"
        assert str(AdjustStrategy.ABSOLUTE) == "AdjustStrategy.ABSOLUTE"
        assert str(AdjustStrategy.RELATIVE) == "AdjustStrategy.RELATIVE"

    def test_enum_equality(self):
        """Test enum equality comparisons."""
        assert AdjustStrategy.PROPORTIONAL == AdjustStrategy.PROPORTIONAL
        assert AdjustStrategy.ABSOLUTE != AdjustStrategy.PROPORTIONAL
        assert AdjustStrategy.RELATIVE != AdjustStrategy.ABSOLUTE