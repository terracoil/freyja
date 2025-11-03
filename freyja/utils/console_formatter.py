"""Console output formatter for dependency analysis results."""

from typing import Dict, Set, List, Optional


class ConsoleFormatter:
  """Format dependency analysis results for console output."""

  def __init__(self, show_classes: bool = True, show_cycles: bool = True, colors: Dict[str, str] = None):
    """Initialize formatter with display options.
    
    :param show_classes: Include class-level dependencies in output
    :param show_cycles: Include circular dependency warnings
    :param colors: Color codes for formatting (optional)
    """
    self.show_classes: bool = show_classes
    self.show_cycles: bool = show_cycles
    self.colors: Dict[str, str] = colors or {
      'red': '',
      'green': '',
      'yellow': '',
      'blue': '',
      'nc': ''  # No Color
    }

  def format_package_dependencies(self, package_deps: Dict[str, Set[str]]) -> str:
    """Format package-level dependencies for display."""
    output = []
    output.append(f"{self.colors['blue']}=== PACKAGE DEPENDENCIES ==={self.colors['nc']}")
    
    # Group by top-level package
    packages = {}
    for module in package_deps:
      parts = module.split('.')
      if len(parts) >= 2:
        package = '.'.join(parts[:2])
      else:
        package = module
      
      if package not in packages:
        packages[package] = []
      packages[package].append(module)
    
    for package in sorted(packages.keys()):
      output.append(f"\n{package}:")
      
      # Collect all dependencies for this package
      all_deps = set()
      for module in packages[package]:
        if module in package_deps:
          all_deps.update(package_deps[module])
      
      # Filter to cross-package dependencies only
      cross_package_deps = set()
      for dep in all_deps:
        dep_parts = dep.split('.')
        if len(dep_parts) >= 2:
          dep_package = '.'.join(dep_parts[:2])
        else:
          dep_package = dep
        
        if dep_package != package and dep_package.startswith('freyja.'):
          cross_package_deps.add(dep_package)
      
      if cross_package_deps:
        for dep in sorted(cross_package_deps):
          output.append(f"  → {dep}")
      else:
        output.append("  → (no cross-package dependencies)")
    
    return '\n'.join(output)

  def format_class_dependencies(self, class_deps: Dict[str, Set[str]], key_classes: List[str] = None) -> str:
    """Format class-level dependencies for display."""
    output = []
    output.append(f"\n{self.colors['blue']}=== KEY CLASS DEPENDENCIES ==={self.colors['nc']}")
    
    # Use provided key classes or detect main classes
    if key_classes is None:
      key_classes = [
        'freyja.freyja_cli.FreyjaCLI',
        'freyja.command.command_discovery.CommandDiscovery',
        'freyja.command.command_executor.CommandExecutor',
        'freyja.cli.execution_coordinator.ExecutionCoordinator',
        'freyja.parser.argument_parser.ArgumentParser',
        'freyja.command.command_tree.CommandTree',
        'freyja.command.command_info.CommandInfo',
      ]
    
    for class_name in key_classes:
      if class_name in class_deps:
        output.append(f"\n{class_name}:")
        deps = class_deps[class_name]
        if deps:
          for dep in sorted(deps):
            output.append(f"  → {dep}")
        else:
          output.append("  → (no class dependencies)")
    
    return '\n'.join(output)

  def format_cycles(self, cycles: List[List[str]]) -> str:
    """Format circular dependency warnings."""
    if not cycles:
      return f"\n{self.colors['green']}✅ No circular dependencies detected{self.colors['nc']}"
    
    output = []
    output.append(f"\n{self.colors['red']}⚠️  CIRCULAR DEPENDENCIES DETECTED:{self.colors['nc']}")
    
    for i, cycle in enumerate(cycles, 1):
      output.append(f"\n{self.colors['red']}Cycle {i}:{self.colors['nc']}")
      cycle_str = ' → '.join(cycle)
      output.append(f"  {cycle_str}")
    
    return '\n'.join(output)

  def format(self, analysis_result: Dict) -> str:
    """Format complete analysis results for console display."""
    output = []
    
    # Extract data from analysis result
    package_deps = analysis_result.get('package_dependencies', {})
    class_deps = analysis_result.get('class_dependencies', {})
    cycles = analysis_result.get('cycles', [])
    
    # Format package dependencies
    if package_deps:
      output.append(self.format_package_dependencies(package_deps))
    
    # Format class dependencies if requested
    if self.show_classes and class_deps:
      output.append(self.format_class_dependencies(class_deps))
    
    # Format circular dependencies if requested
    if self.show_cycles:
      output.append(self.format_cycles(cycles))
    
    return '\n'.join(output)
