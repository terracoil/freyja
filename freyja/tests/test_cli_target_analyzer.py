"""Test suite for TargetAnalyzer."""

import pytest
from freyja.cli import TargetAnalyzer, TargetInfoKeys, TargetMode


class MockClass:
    pass


class MockClassWithDocstring:
    """Mock class with detailed documentation for testing."""
    pass


class AnotherMockClass:
    """Another mock class for multi-class testing."""
    pass


class TestCliTargetAnalyzer:
    """Test TargetAnalyzer functionality."""

    def test_analyze_single_class(self):
        """Test analyzing a single class."""
        analyzer = TargetAnalyzer(MockClass, completion=False, theme_tuner=False)
        mode, info = analyzer.analyze_target()
        
        assert mode == TargetMode.CLASS
        assert info[TargetInfoKeys.PRIMARY_CLASS.value] == MockClass
        assert info[TargetInfoKeys.ALL_CLASSES.value] == [MockClass]
        assert TargetInfoKeys.MODULE.value not in info

    def test_analyze_class_list_single_item(self):
        """Test analyzing a list with one class."""
        analyzer = TargetAnalyzer([MockClass], completion=False, theme_tuner=False)
        mode, info = analyzer.analyze_target()
        
        assert mode == TargetMode.CLASS
        assert info[TargetInfoKeys.PRIMARY_CLASS.value] == MockClass
        assert info[TargetInfoKeys.ALL_CLASSES.value] == [MockClass]

    def test_analyze_class_list_multiple_items(self):
        """Test analyzing a list with multiple classes."""
        classes = [MockClass, AnotherMockClass]
        analyzer = TargetAnalyzer(classes, completion=False, theme_tuner=False)
        mode, info = analyzer.analyze_target()
        
        assert mode == TargetMode.CLASS
        assert info[TargetInfoKeys.PRIMARY_CLASS.value] == AnotherMockClass  # Last class is primary
        assert info[TargetInfoKeys.ALL_CLASSES.value] == classes

    def test_analyze_module(self):
        """Test analyzing a module."""
        import os  # Use os module which should have __file__
        
        analyzer = TargetAnalyzer(os, completion=False, theme_tuner=False)
        mode, info = analyzer.analyze_target()
        
        assert mode == TargetMode.MODULE
        assert info[TargetInfoKeys.MODULE.value] == os
        assert TargetInfoKeys.PRIMARY_CLASS.value not in info
        assert TargetInfoKeys.ALL_CLASSES.value not in info

    def test_analyze_empty_list(self):
        """Test that empty class list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TargetAnalyzer([], completion=False, theme_tuner=False)
        
        assert "Target cannot be None or empty list" in str(exc_info.value)

    def test_analyze_invalid_list_items(self):
        """Test that list with non-class items raises ValueError."""
        analyzer = TargetAnalyzer([MockClass, "not_a_class"], completion=False, theme_tuner=False)
        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze_target()
        
        assert "All items in list must be classes" in str(exc_info.value)

    def test_analyze_invalid_target(self):
        """Test that invalid target types raise ValueError."""
        analyzer = TargetAnalyzer("invalid_target", completion=False, theme_tuner=False)
        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze_target()
        
        assert "Target must be module, class, or list of classes" in str(exc_info.value)

    def test_generate_title_single_class_with_docstring(self):
        """Test title generation for class with docstring."""
        analyzer = TargetAnalyzer(MockClassWithDocstring, completion=False, theme_tuner=False)
        title = analyzer.generate_title()
        
        assert "Mock class with detailed documentation for testing" in title

    def test_generate_title_single_class_without_docstring(self):
        """Test title generation for class without docstring."""
        analyzer = TargetAnalyzer(MockClass, completion=False, theme_tuner=False)
        title = analyzer.generate_title()
        
        assert title == "MockClass"

    def test_generate_title_multiple_classes(self):
        """Test title generation for multiple classes uses primary class."""
        analyzer = TargetAnalyzer([MockClass, MockClassWithDocstring], completion=False, theme_tuner=False)
        title = analyzer.generate_title()
        
        # Should use the last class (primary) for title
        assert "Mock class with detailed documentation for testing" in title

    def test_generate_title_module(self):
        """Test title generation for module."""
        import os
        analyzer = TargetAnalyzer(os, completion=False, theme_tuner=False)
        title = analyzer.generate_title()
        
        assert "Os FreyjaCLI" in title

    def test_generate_title_current_module(self):
        """Test title generation for current module."""
        import json  # Use a simple, reliable module
        analyzer = TargetAnalyzer(json, completion=False, theme_tuner=False)
        title = analyzer.generate_title()
        
        # Should handle module names gracefully
        assert "Json FreyjaCLI" in title


if __name__ == "__main__":
    pytest.main([__file__, "-v"])