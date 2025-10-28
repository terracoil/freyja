# Freyja Remediation Plan - Phased Interactive Execution

**Created**: 2025-10-27
**Status**: Ready for execution
**Approach**: Present each phase → Get approval → Execute → Test → Next phase

---

## 📊 Overall Status

- **Completed**: 1 file (completion/installer.py - 12 violations → 0)
- **Remaining**: ~38 violations across 20+ files
- **Test Status**: All tests passing (2/2 for installer.py)
- **Pattern Established**: ✅ @guarded_expression with implicit returns

---

## Phase 1: completion/base.py - @guarded_expression Conversion

**Priority**: P0 (Critical)
**Files**: `freyja/completion/base.py`
**Risk Level**: LOW (well-tested module, proven pattern)
**Estimated Impact**: -20 lines, 8-9 violations → 0

### Summary

Convert completion/base.py to use @guarded_expression decorator for guard clauses. This file has 8-9 single return-point violations across multiple methods. Using the proven pattern from installer.py, we'll add guards and enable implicit returns.

### Files Touched
- `freyja/completion/base.py`

### Violations to Fix
1. `complete()` - Line 84: Early return inside if block
2. `get_command_group_parser()` - Line 121: Early return inside if block
3. `get_option_values()` - Line 195: Early return inside loop
4. `_complete_file_path()` - Lines 215, 242: Returns inside except blocks
5. `_get_generic_completions()` - Lines 270, 283, 288, 293: Multiple early returns

### Code Preview

**Method 1: `complete()` - BEFORE**
```python
def complete(self) -> None:
    """Handle completion request and output completions."""
    import importlib

    shell = self.detect_shell()
    if not shell:
        return  # ❌ Early return inside if

    # Handle shell-specific completion...
```

**Method 1: `complete()` - AFTER**
```python
@guarded_expression(
    lambda self: self.detect_shell() is not None or "Could not detect shell"
)
def complete(self) -> None:
    """Handle completion request and output completions."""
    import importlib

    shell = self.detect_shell()
    # Handle shell-specific completion...
    # ✅ Implicit return - no return statement needed!
```

**Method 2: `_get_generic_completions()` - BEFORE**
```python
def _get_generic_completions(self, context: CompletionContext) -> list[str]:
    completions: list[str] = []
    parser = context.parser

    if context.command_group_path:
        parser = self.get_command_group_parser(parser, context.command_group_path)
        if not parser:
            return []  # ❌ Early return

    current_word = context.current_word

    if len(context.words) >= 2:
        prev_word = context.words[-2] if len(context.words) >= 2 else ""
        if prev_word.startswith("--"):
            option_values = self.get_option_values(parser, prev_word, current_word)
            if option_values:
                return option_values  # ❌ Early return

    if current_word.startswith("--"):
        options = self.get_available_options(parser)
        return self.complete_partial_word(options, current_word)  # ❌ Early return

    commands = self.get_available_commands(parser)
    if commands:
        return self.complete_partial_word(commands, current_word)  # ❌ Early return

    return completions
```

**Method 2: `_get_generic_completions()` - AFTER**
```python
def _get_generic_completions(self, context: CompletionContext) -> list[str]:
    completions: list[str] = []
    parser = context.parser

    if context.command_group_path:
        parser = self.get_command_group_parser(parser, context.command_group_path)

    if parser:  # Only proceed if parser is valid
        current_word = context.current_word

        # Check option value completion
        if len(context.words) >= 2:
            prev_word = context.words[-2]
            if prev_word.startswith("--"):
                option_values = self.get_option_values(parser, prev_word, current_word)
                if option_values:
                    completions = option_values

        # Complete options if no option values found
        if not completions and current_word.startswith("--"):
            options = self.get_available_options(parser)
            completions = self.complete_partial_word(options, current_word)

        # Complete commands if no options found
        if not completions:
            commands = self.get_available_commands(parser)
            if commands:
                completions = self.complete_partial_word(commands, current_word)

    return completions  # ✅ Single return point
```

### Testing Plan
```bash
# After conversion, run:
poetry run pytest tests/test_completion.py -v
poetry run pytest tests/ -v --tb=short
```

### Success Criteria
- ✅ All 8-9 violations fixed
- ✅ @guarded_expression applied where appropriate
- ✅ Implicit returns used
- ✅ All tests passing
- ✅ No functional regressions

---

## Phase 2: freyja_cli.py - Remaining @guarded_expression Conversions

**Priority**: P0 (Critical)
**Files**: `freyja/freyja_cli.py`
**Risk Level**: LOW (3 methods already fixed, 2 remaining)
**Estimated Impact**: -10 lines, 2 violations → 0

### Summary

Complete the @guarded_expression conversion for freyja_cli.py. Three methods were already fixed earlier. Two remaining methods need conversion.

### Files Touched
- `freyja/freyja_cli.py`

### Violations to Fix
- Identify remaining 2 violations in freyja_cli.py (need to read current file state)
- Apply @guarded_expression pattern
- Enable implicit returns

### Testing Plan
```bash
poetry run pytest tests/test_cli.py -v
poetry run pytest tests/ -v --tb=short
```

---

## Phase 3: cli/execution_coordinator.py - @guarded_expression Conversion

**Priority**: P0 (Critical)
**Files**: `freyja/cli/execution_coordinator.py`
**Risk Level**: MEDIUM (core execution logic)
**Estimated Impact**: -15 lines, 5 violations → 0

### Summary

Convert execution coordinator to use @guarded_expression. This is critical infrastructure code that orchestrates command execution. Will require careful testing.

### Testing Plan
```bash
poetry run pytest tests/test_execution_coordinator.py -v
poetry run pytest tests/ -v --tb=short
```

---

## Phase 4: parser/option_discovery.py - @guarded_expression Conversion

**Priority**: P0 (Critical)
**Files**: `freyja/parser/option_discovery.py`
**Risk Level**: MEDIUM (core parsing logic)
**Estimated Impact**: -15 lines, 5 violations → 0

### Summary

Convert option discovery to use @guarded_expression. This module discovers method parameters and converts them to CLI options.

---

## Phase 5: parser/argument_preprocessor.py - @guarded_expression Conversion

**Priority**: P0 (Critical + 0% Coverage)
**Files**: `freyja/parser/argument_preprocessor.py`
**Risk Level**: HIGH (0% test coverage)
**Estimated Impact**: -12 lines, 4 violations → 0

### Summary

Convert argument preprocessor to use @guarded_expression. **CRITICAL**: This module has 0% test coverage. We need to create tests first or be extremely careful.

### Testing Strategy
```bash
# Manual testing required - no automated tests exist
# Create basic test file first (see Phase 8)
```

---

## Phase 6: parser/positional_handler.py - @guarded_expression Conversion

**Priority**: P0 (Critical)
**Files**: `freyja/parser/positional_handler.py`
**Risk Level**: MEDIUM
**Estimated Impact**: -12 lines, 4 violations → 0

---

## Phase 7: command/command_executor.py - @guarded_expression Conversion

**Priority**: P0 (Critical)
**Files**: `freyja/command/command_executor.py`
**Risk Level**: MEDIUM
**Estimated Impact**: -12 lines, 4 violations → 0

---

## Phase 8: Create Missing Test Files

**Priority**: P0 (Critical - Required for safety)
**Files**:
- `tests/parser/test_argument_preprocessor.py` (NEW)
- `tests/parser/test_command_path_resolver.py` (NEW)

**Risk Level**: LOW (creating tests, not modifying code)
**Estimated Impact**: +200 lines (new test files)

### Summary

Create basic test files for the two modules with 0% coverage. This is CRITICAL before making changes to these modules.

### Test File Structure

**test_argument_preprocessor.py**:
```python
"""Tests for argument preprocessor."""
import pytest
from freyja.parser.argument_preprocessor import ArgumentPreprocessor


def test_preprocessor_reorders_arguments():
    """Test that preprocessor correctly reorders flexible arguments."""
    preprocessor = ArgumentPreprocessor()
    # Test global, sub-global, command argument ordering
    args = ['--global-opt', 'value', 'command', '--cmd-opt', 'value2']
    result = preprocessor.preprocess(args)
    assert result is not None
    # Add proper assertions based on expected behavior


def test_preprocessor_handles_empty_args():
    """Test preprocessor with empty argument list."""
    preprocessor = ArgumentPreprocessor()
    result = preprocessor.preprocess([])
    assert result == []
```

**test_command_path_resolver.py**:
```python
"""Tests for command path resolver."""
import pytest
from freyja.parser.command_path_resolver import CommandPathResolver


def test_resolver_handles_flat_commands():
    """Test resolver with flat double-dash commands."""
    resolver = CommandPathResolver()
    path = resolver.resolve('inner-class--method')
    assert path is not None
    # Add proper assertions


def test_resolver_handles_hierarchical_commands():
    """Test resolver with hierarchical commands."""
    resolver = CommandPathResolver()
    path = resolver.resolve('system completion install')
    assert path is not None
```

---

## Phase 9: Remaining @guarded_expression Conversions

**Priority**: P0 (Critical)
**Files**: 15+ additional files with 1-3 violations each
**Risk Level**: LOW-MEDIUM (smaller changes per file)
**Estimated Impact**: -50 lines total, ~20 violations → 0

### Files to Convert
- `parser/command_path_resolver.py` (3 violations)
- `cli/class_handler.py` (3 violations)
- `parser/command_parser.py` (2 violations)
- `command/command_discovery.py` (2 violations)
- `help/help_formatting_engine.py` (2 violations)
- Additional files with 1-2 violations each

---

## Phase 10: Dependency Injection - freyja_cli.py

**Priority**: P1 (High)
**Files**: `freyja/freyja_cli.py`
**Risk Level**: MEDIUM (architectural change)
**Estimated Impact**: +30 lines, improved testability

### Summary

Add factory injection for hard-coded dependencies:
- ColorFormatter instantiation
- CommandDiscovery instantiation
- CommandExecutor creation

### Code Preview

**BEFORE**:
```python
class FreyjaCLI:
    def __init__(self, *target_classes, theme: bool = True, **kwargs):
        self.discovery = CommandDiscovery(*target_classes, **kwargs)  # ❌ Hard-coded
        # ...

    def _initialize_executors(self) -> dict:
        if self.theme:
            from freyja.theme import ColorFormatter
            color_formatter = ColorFormatter()  # ❌ Hard-coded
```

**AFTER**:
```python
class FreyjaCLI:
    def __init__(
        self,
        *target_classes,
        theme: bool = True,
        discovery_factory: Callable = None,
        color_formatter_factory: Callable = None,
        executor_factory: Callable = None,
        **kwargs
    ):
        factory = discovery_factory or CommandDiscovery
        self.discovery = factory(*target_classes, **kwargs)  # ✅ Injected

        self.color_formatter_factory = color_formatter_factory
        self.executor_factory = executor_factory or CommandExecutor

    def _initialize_executors(self) -> dict:
        color_formatter = None
        if self.theme:
            factory = self.color_formatter_factory or ColorFormatter
            color_formatter = factory()  # ✅ Injected
```

---

## Phase 11: Dependency Injection - execution_coordinator.py

**Priority**: P1 (High)
**Files**: `freyja/cli/execution_coordinator.py`
**Risk Level**: MEDIUM
**Estimated Impact**: +20 lines

---

## Phase 12: Dependency Injection - command_discovery.py

**Priority**: P1 (High)
**Files**: `freyja/command/command_discovery.py`
**Risk Level**: MEDIUM
**Estimated Impact**: +15 lines

---

## Phase 13: Test Quality - Remove capsys Usage

**Priority**: P1 (High)
**Files**: 10+ test files
**Risk Level**: LOW (test changes only)
**Estimated Impact**: Modified ~40 tests

### Summary

Replace capsys-based testing with state/property checks. Add testable properties to classes where needed.

**NOTE**: Explicitly excluded from current remediation unless changes break tests.

---

## Phase 14: Module Reorganization

**Priority**: P2 (Medium)
**Files**: Multiple (shared/, utils/)
**Risk Level**: HIGH (widespread import changes)
**Estimated Impact**: ~30 files touched

### Summary

- Move `shared/` contents to `command/`
- Organize `utils/` into domain packages
- Update all imports throughout codebase

**NOTE**: Deferred until P0/P1 items complete.

---

## Execution Instructions

For each phase:
1. **Present phase** with summary above
2. **Ask**: "Execute this phase? (Yes/No/Other)"
3. **If Yes**: Implement changes, test, commit
4. **If No**: Skip to next phase
5. **If Other**: Wait for user input, then proceed accordingly
6. **After completion**: Present next phase

---

## Success Metrics

**After Phase 9 Complete**:
- ✅ Zero single return-point violations
- ✅ @guarded_expression used throughout
- ✅ All tests passing
- ✅ ~400 line reduction

**After Phase 12 Complete**:
- ✅ No hard-coded dependencies
- ✅ Full dependency injection
- ✅ Improved testability

**Final State**:
- ✅ Full CLAUDE.md compliance
- ✅ Clean, maintainable codebase
- ✅ >90% test coverage
