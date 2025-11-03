"""Dependency analysis utilities for Freyja projects."""

import ast
from pathlib import Path
from typing import Dict, Set, List, Optional, Tuple


class DependencyAnalyzer(ast.NodeVisitor):
  """AST visitor to extract import dependencies and class hierarchies."""

  def __init__(self, project_path: Path, include_external: bool = False, max_depth: int = 10):
    """Initialize analyzer with configuration.
    
    :param project_path: Root path of the project to analyze
    :param include_external: Include external (non-project) dependencies
    :param max_depth: Maximum depth for dependency traversal
    """
    self.project_path: Path = project_path
    self.include_external: bool = include_external
    self.max_depth: int = max_depth
    self.current_module: str = ""
    self.imports: Set[str] = set()
    self.from_imports: Dict[str, Set[str]] = {}
    self.classes: Dict[str, Set[str]] = {}  # class_name -> set of parent classes

  def visit_Import(self, node: ast.Import) -> None:
    """Visit import statements."""
    for alias in node.names:
      self.imports.add(alias.name)
    self.generic_visit(node)

  def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
    """Visit from ... import statements."""
    if node.module:
      if node.module not in self.from_imports:
        self.from_imports[node.module] = set()
      for alias in node.names:
        self.from_imports[node.module].add(alias.name)
    self.generic_visit(node)

  def visit_ClassDef(self, node: ast.ClassDef) -> None:
    """Visit class definitions."""
    bases = []
    for base in node.bases:
      if isinstance(base, ast.Name):
        bases.append(base.id)
      elif isinstance(base, ast.Attribute):
        # Handle module.Class syntax
        parts = []
        current = base
        while isinstance(current, ast.Attribute):
          parts.append(current.attr)
          current = current.value
        if isinstance(current, ast.Name):
          parts.append(current.id)
        bases.append('.'.join(reversed(parts)))

    self.classes[node.name] = set(bases)
    self.generic_visit(node)

  def analyze_file(self, file_path: Path) -> Optional[Dict]:
    """Analyze a single Python file for dependencies."""
    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

      tree = ast.parse(content)
      
      # Reset state for this file
      self.current_module = str(file_path.relative_to(self.project_path.parent))
      self.imports = set()
      self.from_imports = {}
      self.classes = {}
      
      # Visit the AST
      self.visit(tree)

      # Convert module path to package notation
      rel_path = file_path.relative_to(self.project_path.parent)
      module_name = str(rel_path.with_suffix('')).replace('/', '.')

      return {
        'module': module_name,
        'imports': list(self.imports),
        'from_imports': {k: list(v) for k, v in self.from_imports.items()},
        'classes': {k: list(v) for k, v in self.classes.items()},
      }
    except Exception as e:
      print(f"Error analyzing {file_path}: {e}")
      return None

  def analyze(self) -> Dict[str, Dict]:
    """Analyze all Python files in the project."""
    results = {}

    for py_file in self.project_path.rglob('*.py'):
      if '__pycache__' not in str(py_file):
        analysis = self.analyze_file(py_file)
        if analysis:
          results[analysis['module']] = analysis

    return results

  def extract_package_dependencies(self, analysis: Dict[str, Dict]) -> Dict[str, Set[str]]:
    """Extract package-level dependencies from analysis results."""
    package_deps = {}
    project_name = self.project_path.name

    for module, data in analysis.items():
      if not module.startswith(f'{project_name}.'):
        continue

      deps = set()

      # Check from imports
      for from_module, imports in data['from_imports'].items():
        if from_module and from_module.startswith(f'{project_name}.'):
          deps.add(from_module)
        elif from_module and from_module.startswith('.'):
          # Relative import - resolve it
          parts = module.split('.')
          if from_module == '.':
            base = '.'.join(parts[:-1])
          else:
            level = len(from_module) - len(from_module.lstrip('.'))
            base = '.'.join(parts[:-level])
            if from_module.lstrip('.'):
              base = f"{base}.{from_module.lstrip('.')}"
          if base.startswith(f'{project_name}.'):
            deps.add(base)

      # Check direct imports
      for imp in data['imports']:
        if imp.startswith(f'{project_name}.'):
          deps.add(imp)

      package_deps[module] = deps

    return package_deps

  def extract_class_dependencies(self, analysis: Dict[str, Dict]) -> Dict[str, Set[str]]:
    """Extract class-level dependencies from analysis results."""
    class_deps = {}
    project_name = self.project_path.name

    for module, data in analysis.items():
      if not module.startswith(f'{project_name}.'):
        continue

      for class_name, bases in data['classes'].items():
        full_class_name = f"{module}.{class_name}"
        deps = set()

        # Add base class dependencies
        for base in bases:
          if not base.startswith(('ABC', 'Protocol', 'Enum')):
            deps.add(base)

        # Add imports used by this class (heuristic: imported classes)
        for from_module, imports in data['from_imports'].items():
          for imp in imports:
            # If it looks like a class (capitalized)
            if imp and imp[0].isupper() and not imp.startswith('TYPE_'):
              if from_module and from_module.startswith(f'{project_name}.'):
                deps.add(f"{from_module}.{imp}")
              elif from_module and from_module.startswith('.'):
                # Resolve relative import
                parts = module.split('.')
                if from_module == '.':
                  base = '.'.join(parts[:-1])
                else:
                  level = len(from_module) - len(from_module.lstrip('.'))
                  base = '.'.join(parts[:-level])
                  if from_module.lstrip('.'):
                    base = f"{base}.{from_module.lstrip('.')}"
                if base.startswith(f'{project_name}.'):
                  deps.add(f"{base}.{imp}")

        class_deps[full_class_name] = deps

    return class_deps

  def detect_cycles(self, package_deps: Dict[str, Set[str]]) -> List[List[str]]:
    """Detect circular dependencies using DFS."""
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node: str, path: List[str]) -> None:
      visited.add(node)
      rec_stack.add(node)
      current_path = path + [node]

      if node in package_deps:
        for neighbor in package_deps[node]:
          if neighbor in rec_stack:
            # Found cycle
            cycle_start = current_path.index(neighbor)
            cycle = current_path[cycle_start:] + [neighbor]
            cycles.append(cycle)
          elif neighbor not in visited:
            dfs(neighbor, current_path)

      rec_stack.remove(node)

    for node in package_deps:
      if node not in visited:
        dfs(node, [])

    return cycles

  def filter_results(self, analysis: Dict[str, Dict], filter_package: str) -> Dict[str, Dict]:
    """Filter analysis results to specific package."""
    return {
      module: data for module, data in analysis.items()
      if module.startswith(filter_package)
    }
