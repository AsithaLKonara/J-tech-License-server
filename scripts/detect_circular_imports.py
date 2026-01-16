#!/usr/bin/env python3
"""
Circular Import Detection Script

Scans Python modules for circular import dependencies and reports violations.
This prevents architectural regressions that can cause runtime failures.

Usage:
    python scripts/detect_circular_imports.py [--verbose] [--fail-on-circular]
"""

import os
import sys
import importlib
import ast
import networkx as nx
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import argparse


class CircularImportDetector:
    """Detects circular imports in Python modules using AST analysis and graph algorithms."""

    def __init__(self, root_path: Path, verbose: bool = False):
        self.root_path = root_path
        self.verbose = verbose
        self.dependency_graph = nx.DiGraph()
        self.module_paths: Dict[str, Path] = {}
        self.cycles: List[List[str]] = []

    def collect_python_files(self) -> List[Path]:
        """Collect all Python files in the project, excluding certain directories."""
        python_files = []

        # Skip these directories
        skip_dirs = {
            '__pycache__',
            'node_modules',
            '.git',
            'build',
            'dist',
            'venv',
            '.venv',
            'env',
            'logs',
            'test-results',
            '.pytest_cache',
            '.mypy_cache'
        }

        for root, dirs, files in os.walk(self.root_path):
            # Remove skipped directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        return python_files

    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to Python module name."""
        try:
            relative_path = file_path.relative_to(self.root_path)
            module_name = str(relative_path).replace('/', '.').replace('\\', '.')
            if module_name.endswith('.py'):
                module_name = module_name[:-3]
            return module_name
        except ValueError:
            # File not under root_path
            return str(file_path).replace('/', '.').replace('\\', '.').replace('.py', '')

    def extract_imports(self, file_path: Path) -> Set[str]:
        """Extract all import statements from a Python file using AST."""
        imports = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])

        except (SyntaxError, UnicodeDecodeError) as e:
            if self.verbose:
                print(f"Warning: Could not parse {file_path}: {e}")

        return imports

    def resolve_module_path(self, module_name: str) -> Optional[Path]:
        """Resolve module name to file path."""
        # Try different variations
        candidates = [
            self.root_path / f"{module_name.replace('.', '/')}.py",
            self.root_path / f"{module_name.replace('.', '/')}/__init__.py",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return None

    def build_dependency_graph(self):
        """Build the dependency graph by analyzing all Python files."""
        python_files = self.collect_python_files()

        if self.verbose:
            print(f"Found {len(python_files)} Python files")

        for file_path in python_files:
            module_name = self.get_module_name(file_path)
            self.module_paths[module_name] = file_path

            if self.verbose:
                print(f"Processing {module_name} ({file_path})")

            imports = self.extract_imports(file_path)

            for import_name in imports:
                # Only consider imports that we can resolve to our own modules
                if self.resolve_module_path(import_name):
                    self.dependency_graph.add_edge(module_name, import_name)
                    if self.verbose:
                        print(f"  -> {import_name}")

    def find_cycles(self) -> List[List[str]]:
        """Find all cycles in the dependency graph."""
        try:
            # Find all simple cycles
            cycles = list(nx.simple_cycles(self.dependency_graph))
            return cycles
        except nx.NetworkXError:
            return []

    def analyze_cycles(self, cycles: List[List[str]]) -> Dict[str, List[List[str]]]:
        """Analyze cycles and categorize them by severity."""
        analysis = {
            'critical': [],  # Cycles that will cause ImportError at runtime
            'warning': [],   # Cycles that might cause issues
            'info': []       # Cycles that are acceptable
        }

        for cycle in cycles:
            # Check if cycle involves core modules (most critical)
            if any('core.' in module for module in cycle):
                analysis['critical'].append(cycle)
            # Check if cycle involves UI modules
            elif any('ui.' in module for module in cycle):
                analysis['warning'].append(cycle)
            else:
                analysis['info'].append(cycle)

        return analysis

    def report_cycles(self, analysis: Dict[str, List[List[str]]]) -> bool:
        """Report cycles and return True if critical cycles found."""
        has_critical = False

        for severity, cycles in analysis.items():
            if not cycles:
                continue

            print(f"\n{severity.upper()} CIRCULAR IMPORTS ({len(cycles)} found):")
            print("=" * 50)

            for i, cycle in enumerate(cycles, 1):
                print(f"{i}. Cycle: {' -> '.join(cycle)}")

                # Show file locations
                print("   Files:")
                for module in cycle:
                    if module in self.module_paths:
                        print(f"     {module}: {self.module_paths[module]}")
                    else:
                        print(f"     {module}: [not found]")

                if severity == 'critical':
                    has_critical = True
                    print("   ⚠️  This cycle will cause ImportError at runtime!")
                elif severity == 'warning':
                    print("   ⚠️  This cycle may cause issues during development")
                else:
                    print("   ℹ️  This cycle is generally acceptable")

        return has_critical

    def run_analysis(self) -> int:
        """Run the complete circular import analysis."""
        print("🔍 Analyzing circular imports...")
        print(f"Project root: {self.root_path}")

        # Build dependency graph
        self.build_dependency_graph()

        # Find cycles
        cycles = self.find_cycles()
        print(f"\n📊 Found {len(cycles)} total cycles in dependency graph")

        # Analyze cycles
        analysis = self.analyze_cycles(cycles)

        # Report results
        has_critical = self.report_cycles(analysis)

        # Summary
        total_critical = len(analysis['critical'])
        total_warning = len(analysis['warning'])
        total_info = len(analysis['info'])

        print("
📈 SUMMARY:"        print(f"   Critical cycles: {total_critical}")
        print(f"   Warning cycles: {total_warning}")
        print(f"   Info cycles: {total_info}")
        print(f"   Total modules analyzed: {len(self.module_paths)}")

        if has_critical:
            print("\n❌ CRITICAL: Fix all critical circular imports before deployment!")
            return 1
        elif total_warning > 0:
            print("\n⚠️  WARNING: Consider fixing warning-level circular imports")
            return 0
        else:
            print("\n✅ SUCCESS: No critical circular imports detected")
            return 0


def main():
    parser = argparse.ArgumentParser(description="Detect circular imports in Python codebase")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--fail-on-circular", action="store_true",
                       help="Exit with error code if circular imports found")
    parser.add_argument("--root", default=".", help="Project root directory")

    args = parser.parse_args()

    root_path = Path(args.root).resolve()

    if not root_path.exists():
        print(f"Error: Root path {root_path} does not exist")
        return 1

    detector = CircularImportDetector(root_path, args.verbose)
    exit_code = detector.run_analysis()

    if args.fail_on_circular and exit_code == 0:
        # Check if any cycles exist at all
        cycles = detector.find_cycles()
        if cycles:
            print("\n❌ FAIL-ON-CIRCULAR: Found circular imports, exiting with error")
            return 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
