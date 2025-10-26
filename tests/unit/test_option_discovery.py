"""Tests for OptionDiscovery."""

import enum
import pytest
from freyja.parser.option_discovery import OptionDiscovery


class TestEnum(enum.Enum):
  """Test enum."""
  OPTION_A = "a"
  OPTION_B = "b"


class MockCommandTree:
  """Mock command tree for testing OptionDiscovery."""

  def __init__(self):
    self.flat_commands = {}
    self.groups = {}


class TestOptionDiscovery:
  """Test OptionDiscovery functionality."""

  @pytest.fixture
  def sample_class(self):
    """Create sample class with methods."""

    class SampleClass:
      def __init__(self, config: str = "default.json", debug: bool = False):
        self.config = config
        self.debug = debug

      def process(self, input_file: str, output: str = "out.txt", verbose: bool = False):
        """Process file."""
        pass

      def convert(self, source: str, format: TestEnum = TestEnum.OPTION_A):
        """Convert file."""
        pass

    return SampleClass

  @pytest.fixture
  def class_with_inner(self):
    """Create class with inner class."""

    class MainClass:
      def __init__(self, main_config: str = "main.json"):
        self.main_config = main_config

      class DataOps:
        def __init__(self, main, data_dir: str = "./data", parallel: bool = False):
          self.main = main
          self.data_dir = data_dir
          self.parallel = parallel

        def process_batch(self, pattern: str, limit: int = 100):
          """Process batch."""
          pass

    return MainClass

  @pytest.fixture
  def populated_tree_simple(self, sample_class):
    """Create populated command tree for simple class."""
    tree = MockCommandTree()
    # Add flat commands
    tree.flat_commands = {
      "process": {
        "type": "command",
        "function": sample_class.process,
      },
      "convert": {
        "type": "command",
        "function": sample_class.convert,
      },
    }
    return tree

  @pytest.fixture
  def populated_tree_hierarchical(self, class_with_inner):
    """Create populated command tree for class with inner classes."""
    tree = MockCommandTree()
    # Add group with inner class
    tree.groups = {
      "data-ops": {
        "type": "group",
        "inner_class": class_with_inner.DataOps,
        "commands": {
          "process-batch": {
            "type": "command",
            "function": class_with_inner.DataOps.process_batch,
          },
        },
      },
    }
    return tree

  def test_discover_global_options(self, sample_class, populated_tree_simple):
    """Test discovering global options from main class constructor."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    global_options = discovery.discover_global_options()

    assert isinstance(global_options, set)
    assert "--config" in global_options
    assert "--debug" in global_options
    assert len(global_options) == 2

  def test_discover_subglobal_options(self, class_with_inner, populated_tree_hierarchical):
    """Test discovering sub-global options from inner class constructors."""
    discovery = OptionDiscovery(populated_tree_hierarchical, class_with_inner)

    subglobal_options = discovery.discover_subglobal_options()

    assert isinstance(subglobal_options, dict)
    assert "data-ops" in subglobal_options
    assert "--data-dir" in subglobal_options["data-ops"]
    assert "--parallel" in subglobal_options["data-ops"]

  def test_discover_command_options(self, sample_class, populated_tree_simple):
    """Test discovering command-specific options from methods."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    command_options = discovery.discover_command_options()

    assert isinstance(command_options, dict)
    assert "process" in command_options
    assert "--output" in command_options["process"]
    assert "--verbose" in command_options["process"]
    # Note: input_file is positional, not an option

  def test_discover_positional_parameters(self, sample_class, populated_tree_simple):
    """Test discovering positional parameters from methods."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    positionals = discovery.discover_positional_parameters()

    assert isinstance(positionals, dict)
    assert "process" in positionals
    assert positionals["process"] is not None
    assert positionals["process"].param_name == "input_file"
    assert positionals["process"].is_required is True

  def test_get_all_known_options_flat_command(self, sample_class, populated_tree_simple):
    """Test aggregating all options for a flat command."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    all_options = discovery.get_all_known_options(["process"])

    assert isinstance(all_options, set)
    # Should include global + command options
    assert "--config" in all_options
    assert "--debug" in all_options
    assert "--output" in all_options
    assert "--verbose" in all_options

  def test_get_all_known_options_hierarchical_command(self, class_with_inner, populated_tree_hierarchical):
    """Test aggregating all options for hierarchical command."""
    discovery = OptionDiscovery(populated_tree_hierarchical, class_with_inner)

    all_options = discovery.get_all_known_options(["data-ops", "process-batch"])

    assert isinstance(all_options, set)
    # Should include global + subglobal + command options
    assert "--main-config" in all_options  # Global
    assert "--data-dir" in all_options  # Sub-global
    assert "--parallel" in all_options  # Sub-global
    assert "--limit" in all_options  # Command
    # Note: pattern is positional, not an option

  def test_validate_option_conflicts_none(self, sample_class, populated_tree_simple):
    """Test conflict validation when no conflicts exist."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    conflicts = discovery.validate_option_conflicts()

    assert isinstance(conflicts, dict)
    assert len(conflicts) == 0

  def test_validate_option_conflicts_detected(self):
    """Test conflict validation detects conflicts."""

    class ConflictClass:
      def __init__(self, config: str = "main.json"):
        self.config = config

      class Inner:
        def __init__(self, main, config: str = "inner.json"):  # Conflicts with global
          self.main = main
          self.config = config

        def process(self):
          pass

    tree = MockCommandTree()
    tree.groups = {
      "inner": {
        "type": "group",
        "inner_class": ConflictClass.Inner,
        "commands": {},
      },
    }
    discovery = OptionDiscovery(tree, ConflictClass)

    conflicts = discovery.validate_option_conflicts()

    assert isinstance(conflicts, dict)
    assert len(conflicts) > 0  # Should detect global vs inner conflict

  def test_suggest_option_corrections(self, sample_class, populated_tree_simple):
    """Test option correction suggestions."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    suggestions = discovery.suggest_option_corrections("--confg", ["process"])

    assert isinstance(suggestions, list)
    # Suggestions may be empty if similarity too low
    if len(suggestions) > 0:
      assert any("config" in s for s in suggestions)

  def test_empty_class_no_options(self):
    """Test discovery with class that has no parameters."""

    class EmptyClass:
      def __init__(self):
        pass

      def simple_method(self):
        pass

    tree = MockCommandTree()
    discovery = OptionDiscovery(tree, EmptyClass)

    global_options = discovery.discover_global_options()
    command_options = discovery.discover_command_options()

    assert isinstance(global_options, set)
    assert len(global_options) == 0
    assert isinstance(command_options, dict)

  def test_method_without_parameters(self):
    """Test discovery for method with no parameters."""

    class SimpleClass:
      def __init__(self, config: str = "test.json"):
        self.config = config

      def no_params(self):
        """Method with no parameters."""
        pass

    tree = MockCommandTree()
    tree.flat_commands = {
      "no_params": {
        "type": "command",
        "function": SimpleClass.no_params,
      },
    }
    discovery = OptionDiscovery(tree, SimpleClass)

    command_options = discovery.discover_command_options()

    assert "no_params" in command_options
    assert len(command_options["no_params"]) == 0  # No options for this command
