#!/usr/bin/env python3
"""Analyze Freyja codebase dependencies."""

import ast
import os
from pathlib import Path
from typing import Dict, Set, Tuple
import json


class DependencyAnalyzer(ast.NodeVisitor):
    """AST visitor to extract import dependencies."""
    
    def __init__(self, module_path: str):
        self.module_path = module_path
        self.imports: Set[str] = set()
        self.from_imports: Dict[str, Set[str]] = {}
        self.classes: Dict[str, Set[str]] = {}  # class_name -> set of parent classes
        
    def visit_Import(self, node):
        """Visit import statements."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Visit from ... import statements."""
        if node.module:
            if node.module not in self.from_imports:
                self.from_imports[node.module] = set()
            for alias in node.names:
                self.from_imports[node.module].add(alias.name)
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
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


def analyze_file(file_path: Path) -> Dict:
    """Analyze a single Python file for dependencies."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        analyzer = DependencyAnalyzer(str(file_path))
        analyzer.visit(tree)
        
        # Convert module path to package notation
        rel_path = file_path.relative_to(Path.cwd())
        module_name = str(rel_path.with_suffix('')).replace('/', '.')
        
        return {
            'module': module_name,
            'imports': list(analyzer.imports),
            'from_imports': {k: list(v) for k, v in analyzer.from_imports.items()},
            'classes': {k: list(v) for k, v in analyzer.classes.items()},
        }
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return None


def analyze_package(package_path: Path) -> Dict[str, Dict]:
    """Analyze all Python files in a package."""
    results = {}
    
    for py_file in package_path.rglob('*.py'):
        if '__pycache__' not in str(py_file):
            analysis = analyze_file(py_file)
            if analysis:
                results[analysis['module']] = analysis
    
    return results


def extract_freyja_dependencies(analysis: Dict[str, Dict]) -> Dict[str, Set[str]]:
    """Extract only freyja-internal dependencies."""
    freyja_deps = {}
    
    for module, data in analysis.items():
        if not module.startswith('freyja.'):
            continue
            
        deps = set()
        
        # Check from imports
        for from_module, imports in data['from_imports'].items():
            if from_module and from_module.startswith('freyja.'):
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
                if base.startswith('freyja.'):
                    deps.add(base)
        
        # Check direct imports
        for imp in data['imports']:
            if imp.startswith('freyja.'):
                deps.add(imp)
        
        freyja_deps[module] = deps
    
    return freyja_deps


def get_class_dependencies(analysis: Dict[str, Dict]) -> Dict[str, Dict[str, Set[str]]]:
    """Extract class-level dependencies."""
    class_deps = {}
    
    for module, data in analysis.items():
        if not module.startswith('freyja.'):
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
                        if from_module and from_module.startswith('freyja.'):
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
                            if base.startswith('freyja.'):
                                deps.add(f"{base}.{imp}")
            
            class_deps[full_class_name] = deps
    
    return class_deps


def main():
    """Main analysis function."""
    freyja_path = Path.cwd() / 'freyja'
    
    print("Analyzing Freyja codebase dependencies...")
    analysis = analyze_package(freyja_path)
    
    # Extract package dependencies
    package_deps = extract_freyja_dependencies(analysis)
    
    # Extract class dependencies
    class_deps = get_class_dependencies(analysis)
    
    # Group by package
    packages = {}
    for module in package_deps:
        parts = module.split('.')
        if len(parts) >= 2:
            package = '.'.join(parts[:2])
        else:
            package = module
        
        if package not in packages:
            packages[package] = {
                'modules': [],
                'dependencies': set(),
                'classes': {}
            }
        
        packages[package]['modules'].append(module)
        packages[package]['dependencies'].update(package_deps[module])
    
    # Add class info to packages
    for full_class, deps in class_deps.items():
        module = '.'.join(full_class.split('.')[:-1])
        class_name = full_class.split('.')[-1]
        
        parts = module.split('.')
        if len(parts) >= 2:
            package = '.'.join(parts[:2])
        else:
            package = module
            
        if package in packages:
            packages[package]['classes'][class_name] = {
                'full_name': full_class,
                'dependencies': list(deps)
            }
    
    # Clean up package dependencies (only keep cross-package deps)
    for package, info in packages.items():
        cleaned_deps = set()
        for dep in info['dependencies']:
            dep_parts = dep.split('.')
            if len(dep_parts) >= 2:
                dep_package = '.'.join(dep_parts[:2])
            else:
                dep_package = dep
            
            if dep_package != package and dep_package.startswith('freyja.'):
                cleaned_deps.add(dep_package)
        
        info['dependencies'] = list(sorted(cleaned_deps))
    
    # Output results
    print("\n=== PACKAGE DEPENDENCIES ===")
    for package in sorted(packages.keys()):
        print(f"\n{package}:")
        deps = packages[package]['dependencies']
        if deps:
            for dep in sorted(deps):
                print(f"  → {dep}")
        else:
            print("  → (no cross-package dependencies)")
    
    print("\n\n=== KEY CLASS DEPENDENCIES ===")
    # Focus on main classes
    key_classes = [
        'freyja.freyja_cli.FreyjaCLI',
        'freyja.command.CommandDiscovery',
        'freyja.command.CommandExecutor',
        'freyja.command.CommandParser',
        'freyja.command.ExecutionCoordinator',
        'freyja.parser.ArgumentParser',
        'freyja.shared.CommandTree',
        'freyja.shared.CommandInfo',
    ]
    
    for class_name in key_classes:
        if class_name in class_deps:
            print(f"\n{class_name}:")
            deps = class_deps[class_name]
            if deps:
                for dep in sorted(deps):
                    print(f"  → {dep}")
            else:
                print("  → (no class dependencies)")
    
    # Save full results to JSON
    output = {
        'packages': packages,
        'class_dependencies': {k: list(v) for k, v in class_deps.items()}
    }
    
    with open('freyja_dependencies.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n\nFull analysis saved to freyja_dependencies.json")


if __name__ == '__main__':
    main()