"""Test suite for CliTargetAnalyzer."""

import pytest
import types
from freyja.command.cli_target_analyzer import CliTargetAnalyzer
from freyja.enums.target_mode import TargetMode
from freyja.enums.target_info_keys import TargetInfoKeys


class MockClass:
    pass


class MockClassWithDocstring:
    """Mock class with detailed documentation for testing."""
    pass


class AnotherMockClass:
    """Another mock class for multi-class testing."""
    pass


class TestCliTargetAnalyzer:
    """Test CliTargetAnalyzer functionality."""

    def test_analyze_single_class(self):
        """Test analyzing a single class."""
        mode, info = CliTargetAnalyzer.analyze_target(MockClass)
        
        assert mode == TargetMode.CLASS
        assert info[TargetInfoKeys.PRIMARY_CLASS.value] == MockClass
        assert info[TargetInfoKeys.ALL_CLASSES.value] == [MockClass]
        assert TargetInfoKeys.MODULE.value not in info

    def test_analyze_class_list_single_item(self):
        """Test analyzing a list with one class."""
        mode, info = CliTargetAnalyzer.analyze_target([MockClass])
        
        assert mode == TargetMode.CLASS
        assert info[TargetInfoKeys.PRIMARY_CLASS.value] == MockClass
        assert info[TargetInfoKeys.ALL_CLASSES.value] == [MockClass]

    def test_analyze_class_list_multiple_items(self):
        """Test analyzing a list with multiple classes."""
        classes = [MockClass, AnotherMockClass]
        mode, info = CliTargetAnalyzer.analyze_target(classes)
        
        assert mode == TargetMode.CLASS
        assert info[TargetInfoKeys.PRIMARY_CLASS.value] == AnotherMockClass  # Last class is primary
        assert info[TargetInfoKeys.ALL_CLASSES.value] == classes

    def test_analyze_module(self):
        """Test analyzing a module."""
        import os  # Use os module which should have __file__
        
        mode, info = CliTargetAnalyzer.analyze_target(os)
        
        assert mode == TargetMode.MODULE
        assert info[TargetInfoKeys.MODULE.value] == os
        assert TargetInfoKeys.PRIMARY_CLASS.value not in info
        assert TargetInfoKeys.ALL_CLASSES.value not in info

    def test_analyze_empty_list(self):
        """Test that empty class list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            CliTargetAnalyzer.analyze_target([])
        
        assert "Class list cannot be empty" in str(exc_info.value)

    def test_analyze_invalid_list_items(self):
        """Test that list with non-class items raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            CliTargetAnalyzer.analyze_target([MockClass, "not_a_class"])
        
        assert "All items in list must be classes" in str(exc_info.value)

    def test_analyze_invalid_target(self):
        """Test that invalid target types raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            CliTargetAnalyzer.analyze_target("invalid_target")
        
        assert "Target must be module, class, or list of classes" in str(exc_info.value)

    def test_generate_title_single_class_with_docstring(self):
        """Test title generation for class with docstring."""
        title = CliTargetAnalyzer.generate_title(MockClassWithDocstring)
        
        assert "Mock class with detailed documentation for testing" in title

    def test_generate_title_single_class_without_docstring(self):
        """Test title generation for class without docstring."""
        title = CliTargetAnalyzer.generate_title(MockClass)
        
        assert title == "MockClass"

    def test_generate_title_multiple_classes(self):
        """Test title generation for multiple classes uses primary class."""
        title = CliTargetAnalyzer.generate_title([MockClass, MockClassWithDocstring])
        
        # Should use the last class (primary) for title
        assert "Mock class with detailed documentation for testing" in title

    def test_generate_title_module(self):
        """Test title generation for module."""
        import os
        title = CliTargetAnalyzer.generate_title(os)
        
        assert "Os CLI" in title

    def test_generate_title_current_module(self):
        """Test title generation for current module."""
        import json  # Use a simple, reliable module
        title = CliTargetAnalyzer.generate_title(json)
        
        # Should handle module names gracefully
        assert "Json CLI" in title


if __name__ == "__main__":
    pytest.main([__file__, "-v"])