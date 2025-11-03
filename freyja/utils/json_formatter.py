"""JSON output formatter for dependency analysis results."""

import json
from typing import Dict, Any


class JsonFormatter:
  """Format dependency analysis results as JSON."""

  def __init__(self, pretty: bool = True, indent: int = 2):
    """Initialize JSON formatter.
    
    :param pretty: Use pretty formatting with indentation
    :param indent: Number of spaces for indentation when pretty=True
    """
    self.pretty: bool = pretty
    self.indent: int = indent

  def format(self, analysis_result: Dict[str, Any]) -> str:
    """Format analysis results as JSON string."""
    # Convert sets to lists for JSON serialization
    serializable_result = self._make_serializable(analysis_result)
    
    if self.pretty:
      return json.dumps(serializable_result, indent=self.indent, sort_keys=True)
    else:
      return json.dumps(serializable_result, sort_keys=True)

  def _make_serializable(self, obj: Any) -> Any:
    """Convert non-serializable objects (like sets) to serializable equivalents."""
    if isinstance(obj, dict):
      return {key: self._make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
      return [self._make_serializable(item) for item in obj]
    elif isinstance(obj, set):
      return sorted(list(obj))  # Convert sets to sorted lists
    else:
      return obj
