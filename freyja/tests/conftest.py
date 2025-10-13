"""Test configuration and fixtures for freyja tests."""

import enum
from pathlib import Path

import pytest


class TestEnum(enum.Enum):
    """Test enumeration for FreyjaCLI testing."""

    OPTION_A = 1
    OPTION_B = 2
    OPTION_C = 3


def sample_function(name: str = "world", count: int = 1):
    """Sample function with docstring parameters.

    :param name: The name to greet in the message
    :param count: Number of times to repeat the greeting
    """
    return f"Hello {name}! " * count


def function_with_types(
    text: str,
    number: int = 42,
    ratio: float = 3.14,
    active: bool = False,
    choice: TestEnum = TestEnum.OPTION_A,
    file_path: Path | None = None,
):
    """Function with various type annotations.

    :param text: Required text input parameter
    :param number: Optional integer with default value
    :param ratio: Optional float with default value
    :param active: Boolean flag parameter
    :param choice: Enumeration choice parameter
    :param file_path: Optional file path parameter
    """
    return {
        "text": text,
        "number": number,
        "ratio": ratio,
        "active": active,
        "choice": choice,
        "file_path": file_path,
    }


def function_without_docstring():
    """Function without parameter docstrings."""
    return "No docstring parameters"


def function_with_args_kwargs(required: str, *args, **kwargs):
    """Function with *args and **kwargs.

    :param required: Required parameter
    """
    return f"Required: {required}, args: {args}, kwargs: {kwargs}"


class SampleTestClass:
    """Sample class for testing."""

    def __init__(self, config: str = "test.json", debug: bool = False):
        self.config = config
        self.debug = debug

    def sample_method(self, name: str = "world", count: int = 1):
        """Sample method with parameters."""
        return f"Hello {name}! " * count

    def method_with_types(
        self,
        text: str,
        number: int = 42,
        ratio: float = 3.14,
        active: bool = False,
        choice: TestEnum = TestEnum.OPTION_A,
        file_path: Path | None = None,
    ):
        """Method with various type annotations."""
        return {
            "text": text,
            "number": number,
            "ratio": ratio,
            "active": active,
            "choice": choice,
            "file_path": file_path,
        }


@pytest.fixture
def sample_test_class():
    """Provide a sample class for testing."""
    return SampleTestClass


@pytest.fixture
def sample_function_opts():
    """Provide sample function options for backward compatibility tests."""
    return {
        "sample_function": {"description": "Sample function for testing"},
        "function_with_types": {"description": "Function with various types"},
    }


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark certain tests as slow."""
    for item in items:
        if "external_links" in item.nodeid:
            item.add_marker(pytest.mark.slow)
