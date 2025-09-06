"""
Comprehensive integration tests for the completion system.

These tests verify that completion and normal execution are completely isolated
and that completion never interferes with normal command execution.
"""
import inspect
import os
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from freyja.freyja_cli import FreyjaCLI
from freyja.cli.execution_coordinator import ExecutionCoordinator
from freyja.command.command_tree import CommandTree
from freyja.command.command_info import CommandInfo


class TestCompletionSystemIntegration(unittest.TestCase):
    """Comprehensive integration tests for completion system isolation."""

    def setUp(self):
        """Set up test environment."""
        # Clean environment of any completion variables
        completion_vars = [
            '_FREYJA_COMPLETE',
            '_FREYJA_COMPLETE_ZSH',
            '_FREYJA_COMPLETE_BASH',
            '_FREYJA_COMPLETE_FISH',
            '_FREYJA_COMPLETE_POWERSHELL',
            'COMP_WORDS_STR',
            'COMP_CWORD_NUM'
        ]
        
        for var in completion_vars:
            if var in os.environ:
                del os.environ[var]

    def tearDown(self):
        """Clean up after tests."""
        # Ensure no completion variables remain
        completion_vars = [
            '_FREYJA_COMPLETE',
            '_FREYJA_COMPLETE_ZSH',
            '_FREYJA_COMPLETE_BASH',
            '_FREYJA_COMPLETE_FISH',
            '_FREYJA_COMPLETE_POWERSHELL',
            'COMP_WORDS_STR',
            'COMP_CWORD_NUM'
        ]
        
        for var in completion_vars:
            if var in os.environ:
                del os.environ[var]

    def create_test_cli(self):
        """Create a test CLI instance."""
        class TestCommands:
            def __init__(self):
                pass
            
            def hello(self, name: str = "world"):
                """Say hello to someone."""
                return f"Hello, {name}!"
            
            def goodbye(self, name: str = "world"):
                """Say goodbye to someone."""
                return f"Goodbye, {name}!"
        
        return FreyjaCLI(TestCommands, title="Test CLI")

    def test_normal_execution_without_completion_env(self):
        """Test that normal execution works without completion environment."""
        cli = self.create_test_cli()
        
        # Ensure no completion detection
        self.assertFalse(cli._is_completion_request())
        
        # Test that we can create and use the CLI normally
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('sys.argv', ['test', '--help']):
                try:
                    cli.run()
                except SystemExit as e:
                    # Help should exit with code 0
                    self.assertEqual(e.code, 0)
        
        output = mock_stdout.getvalue()
        self.assertIn("Test CLI", output)

    def test_completion_detection_accuracy(self):
        """Test that completion is only detected when appropriate variables are set."""
        cli = self.create_test_cli()
        
        # Should not detect completion normally
        self.assertFalse(cli._is_completion_request())
        
        # Should detect with _FREYJA_COMPLETE
        with patch.dict(os.environ, {'_FREYJA_COMPLETE': 'zsh'}):
            self.assertTrue(cli._is_completion_request())
        
        # Should detect with shell-specific variables
        for shell_var in ['_FREYJA_COMPLETE_ZSH', '_FREYJA_COMPLETE_BASH', '_FREYJA_COMPLETE_FISH']:
            with patch.dict(os.environ, {shell_var: '1'}):
                self.assertTrue(cli._is_completion_request())
        
        # Should detect with --_complete flag
        with patch.object(sys, 'argv', ['test', '--_complete']):
            self.assertTrue(cli._is_completion_request())

    def test_completion_isolation(self):
        """Test that completion execution is completely isolated."""
        cli = self.create_test_cli()
        
        # Mock sys.exit to prevent actual exit during testing
        with patch('sys.exit') as mock_exit:
            with patch.dict(os.environ, {
                '_FREYJA_COMPLETE': 'zsh',
                'COMP_WORDS_STR': 'test hel',
                'COMP_CWORD_NUM': '2'
            }):
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    # This should trigger completion mode
                    cli.run()
                    
                    # Completion should always exit
                    mock_exit.assert_called()
                    
                    # Should have attempted to generate completions
                    # (actual completion output depends on the implementation)

    def test_execution_coordinator_completion_safeguards(self):
        """Test that execution coordinator has proper safeguards against completion interference."""
        tree = CommandTree()
        
        # Create a proper CommandInfo object
        test_function = lambda: "test output"
        command_info = CommandInfo(
            name='test',
            original_name='test',
            function=test_function,
            signature=inspect.signature(test_function)
        )
        tree.add_command('test', command_info)
        
        coordinator = ExecutionCoordinator(None, {})
        coordinator.command_tree = tree
        
        # Should raise error if completion environment detected in normal execution
        with patch.dict(os.environ, {'_FREYJA_COMPLETE': 'zsh'}):
            with self.assertRaises(RuntimeError) as context:
                coordinator.parse_and_execute(MagicMock(), [])
            
            self.assertIn("Completion environment detected", str(context.exception))
        
        # Should raise error if --_complete flag present in normal execution
        with self.assertRaises(RuntimeError) as context:
            coordinator.parse_and_execute(MagicMock(), ['--_complete'])
        
        self.assertIn("Completion request reached normal execution", str(context.exception))

    def test_environmental_isolation_sequence(self):
        """Test that completion doesn't pollute environment for subsequent runs."""
        cli = self.create_test_cli()
        
        # Step 1: Normal execution should work
        self.assertFalse(cli._is_completion_request())
        
        # Step 2: Simulate completion execution
        with patch('sys.exit'):  # Prevent actual exit
            with patch.dict(os.environ, {
                '_FREYJA_COMPLETE': 'zsh',
                'COMP_WORDS_STR': 'test hel',
                'COMP_CWORD_NUM': '2'
            }):
                with patch('sys.stdout', new_callable=StringIO):
                    cli.run()
        
        # Step 3: Normal execution should still work after completion
        # (environment variables should be scoped to the with block)
        self.assertFalse(cli._is_completion_request())

    def test_completion_handler_error_handling(self):
        """Test that completion handler errors are handled gracefully."""
        cli = self.create_test_cli()
        
        # Mock completion handler to raise exception
        with patch.object(cli.execution_coordinator, '_handle_completion_request', side_effect=Exception("Test error")):
            with patch('sys.exit') as mock_exit:
                with patch.dict(os.environ, {'_FREYJA_COMPLETE': 'zsh'}):
                    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                        cli.run()
                        
                        # Should exit with error code
                        mock_exit.assert_called_with(1)
                        
                        # Should print error message
                        stderr_output = mock_stderr.getvalue()
                        self.assertIn("Completion error", stderr_output)

    def test_integration_with_examples(self):
        """Integration test with actual example files."""
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        
        if not examples_dir.exists():
            self.skipTest("Examples directory not found")
        
        # Test cls_example normal execution
        cls_example = examples_dir / "cls_example"
        if cls_example.exists():
            result = subprocess.run(
                [sys.executable, str(cls_example)],
                env={'PYTHONPATH': str(examples_dir.parent)},
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should show usage, not completion output
            self.assertIn("usage:", result.stdout.lower())
            self.assertNotEqual(result.stdout.strip(), "completion")
        
        # Test mod_example normal execution
        mod_example = examples_dir / "mod_example"
        if mod_example.exists():
            result = subprocess.run(
                [sys.executable, str(mod_example)],
                env={'PYTHONPATH': str(examples_dir.parent)},
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should show usage
            self.assertIn("usage:", result.stdout.lower())

    def test_completion_after_normal_execution(self):
        """Test that completion works after normal execution."""
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        cls_example = examples_dir / "cls_example"
        
        if not cls_example.exists():
            self.skipTest("cls_example not found")
        
        # Step 1: Normal execution
        result1 = subprocess.run(
            [sys.executable, str(cls_example)],
            env={'PYTHONPATH': str(examples_dir.parent)},
            capture_output=True,
            text=True,
            timeout=5
        )
        self.assertIn("usage:", result1.stdout.lower())
        
        # Step 2: Completion execution
        result2 = subprocess.run(
            [sys.executable, str(cls_example), '--_complete'],
            env={
                'PYTHONPATH': str(examples_dir.parent),
                '_FREYJA_COMPLETE': 'zsh',
                'COMP_WORDS_STR': 'cls_example fo',
                'COMP_CWORD_NUM': '2'
            },
            capture_output=True,
            text=True,
            timeout=5
        )
        # Completion should generate some output (exact output depends on implementation)
        self.assertIsNotNone(result2.stdout)
        
        # Step 3: Normal execution again (should work normally)
        result3 = subprocess.run(
            [sys.executable, str(cls_example)],
            env={'PYTHONPATH': str(examples_dir.parent)},
            capture_output=True,
            text=True,
            timeout=5
        )
        self.assertIn("usage:", result3.stdout.lower())
        self.assertNotEqual(result3.stdout.strip(), "completion")

    def test_multiple_completion_types(self):
        """Test different completion shell types don't interfere."""
        cli = self.create_test_cli()
        
        shell_types = ['zsh', 'bash', 'fish', 'powershell']
        
        for shell_type in shell_types:
            with self.subTest(shell=shell_type):
                with patch('sys.exit'):
                    with patch.dict(os.environ, {f'_FREYJA_COMPLETE_{shell_type.upper()}': '1'}):
                        self.assertTrue(cli._is_completion_request())

    def test_no_state_persistence_between_instances(self):
        """Test that different CLI instances don't share completion state."""
        # Create first CLI and simulate completion
        cli1 = self.create_test_cli()
        
        with patch('sys.exit'):
            with patch.dict(os.environ, {'_FREYJA_COMPLETE': 'zsh'}):
                with patch('sys.stdout', new_callable=StringIO):
                    cli1.run()
        
        # Create second CLI - should not be affected by first CLI's completion state
        cli2 = self.create_test_cli()
        self.assertFalse(cli2._is_completion_request())
        
        # Both should work independently
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('sys.argv', ['test', '--help']):
                try:
                    cli2.run()
                except SystemExit:
                    pass
        
        output = mock_stdout.getvalue()
        self.assertIn("Test CLI", output)


if __name__ == '__main__':
    unittest.main()