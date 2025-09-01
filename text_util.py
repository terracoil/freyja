"""Centralized string utilities for FreyjaCLI generation with caching."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Dict, Sequence


class TextUtil:
  """Centralized string conversion utilities with performance optimizations."""

  # Cache for converted strings to avoid repeated operations
  _conversion_cache: Dict[str, str] = {}

  @classmethod
  def jsonify(cls, obj: any, *args, **kwargs) -> str:
    # print(f"\n\n{type(obj)}: {isinstance(obj, list)} / {isinstance(obj, dict)}\n\n")
    return json.dumps(cls.collectify(obj), indent=4, sort_keys=True)


  @classmethod
  def collectify(cls, obj):
    def _filter(d):
      return {k:v for k,v in d.items() if not k.startswith("_")}

    if isinstance(obj, type):
      result=cls.collectify(_filter(obj.__dict__))
    elif isinstance(obj, dict):
      result={k:cls.collectify(v) for k, v in obj.items()}
    elif isinstance(obj, list):
      result= [cls.collectify(o) for o in obj]
    elif hasattr(obj, '__dict__'):
      result=cls.collectify(_filter(vars(obj)))
    else:
      result = str(obj)

    return result




  @classmethod
  @lru_cache(maxsize=256)
  def kebab_case(cls, text: str) -> str:
    """
    Convert any string format to kebab-case.

    Handles camelCase, PascalCase, snake_case, and mixed formats.
    FreyjaCLI conventions favor kebab-case for better readability and consistency across shells.
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
  def snake_case(cls, text: str) -> str:
    """Map FreyjaCLI argument names back to Python function parameters.

    Enables seamless integration between FreyjaCLI parsing and function invocation.
    """
    return text.replace('-', '_').lower()

# def format_pretty(text: str, *args, **kwargs):
#   print(str)
#   print(f"Args: {[v for v in args]}")
#   print(f"KWArgs: {{k:v for k, v in kwargs.items()}}")

  @staticmethod
  # @lru_cache(maxsize=256)
  def format_pretty(text: str, *args, **kwargs) -> str:
    formatted_args = [TextUtil.jsonify(v) for v in args]
    formatted_kwargs = {k: TextUtil.jsonify(v) for k, v in kwargs.items()}
    return text.format(*formatted_args, **formatted_kwargs)

  @staticmethod
  def pprint(text: str, *args, **kwargs):
    """
    Pretty print a string with given args and kwargs, which are formatted using JSON if possible
    :param text: The base string to be formatted and printed
    :return:
    """
    print(TextUtil.format_pretty(text, *args, **kwargs))

  @classmethod
  def clear_cache(cls) -> None:
    """Reset string conversion cache for testing isolation.

    Prevents test interdependencies by ensuring clean state between test runs.
    """
    TextUtil.kebab_case.cache_clear()
    TextUtil.snake_case.cache_clear()
    TextUtil.format_pretty.cache_clear()
    TextUtil._conversion_cache.clear()

  @classmethod
  def get_cache_info(cls, **kwarg) -> dict:
    """Get cache statistics for performance monitoring."""
    return {
      'format_pretty': TextUtil.format_pretty.cache_info()._asdict(),
      'kebab_case': TextUtil.kebab_case.cache_info()._asdict(),
      'kebab_to_snake': TextUtil.snake_case.cache_info()._asdict(),
      'conversion_cache_size': len(TextUtil._conversion_cache)
    }
