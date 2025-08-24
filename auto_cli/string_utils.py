"""Centralized string utilities for CLI generation with caching."""

import re
from functools import lru_cache
from typing import Dict


class StringUtils:
    """Centralized string conversion utilities with performance optimizations."""

    # Cache for converted strings to avoid repeated operations
    _conversion_cache: Dict[str, str] = {}

    @classmethod
    @lru_cache(maxsize=256)
    def kebab_case(cls, text: str) -> str:
        """
        Convert any string format to kebab-case.

        Handles camelCase, PascalCase, snake_case, and mixed formats.
        CLI conventions favor kebab-case for better readability and consistency across shells.
        """
        if not text:
            return text

        # Handle snake_case to kebab-case
        result = text.replace('_', '-')

        # Insert dash before uppercase letters that follow lowercase letters or digits
        # This handles cases like "fooBar" -> "foo-Bar"
        result = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', result)

        # Insert dash before uppercase letters that are followed by lowercase letters
        # This handles cases like "XMLHttpRequest" -> "XML-Http-Request"
        result = re.sub(r'([A-Z])([A-Z][a-z])', r'\1-\2', result)

        return result.lower()

    @classmethod
    @lru_cache(maxsize=256)
    def kebab_to_snake(cls, text: str) -> str:
        """Map CLI argument names back to Python function parameters.

        Enables seamless integration between CLI parsing and function invocation.
        """
        return text.replace('-', '_')

    @classmethod
    def clear_cache(cls) -> None:
        """Reset string conversion cache for testing isolation.

        Prevents test interdependencies by ensuring clean state between test runs.
        """
        StringUtils.kebab_case.cache_clear()
        StringUtils.kebab_case.cache_clear()
        StringUtils.kebab_to_snake.cache_clear()
        StringUtils.kebab_case.cache_clear()
        StringUtils._conversion_cache.clear()

    @classmethod
    def get_cache_info(cls) -> dict:
        """Get cache statistics for performance monitoring."""
        return {
            'kebab_case': StringUtils.kebab_case.cache_info()._asdict(),
            'kebab_to_snake': StringUtils.kebab_to_snake.cache_info()._asdict(),
            'conversion_cache_size': len(StringUtils._conversion_cache)
        }
