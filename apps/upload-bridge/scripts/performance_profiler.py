#!/usr/bin/env python3
"""
Performance Profiler for Upload Bridge

Analyzes startup performance, identifies bottlenecks, and provides optimization recommendations.

Usage:
    python scripts/performance_profiler.py [--profile-startup] [--analyze-imports] [--generate-report]
"""

import time
import sys
import cProfile
import pstats
import io
from pathlib import Path
import argparse
import subprocess
import psutil
import os
from typing import Dict, List, Any, Optional
import gc


class PerformanceProfiler:
    """Comprehensive performance analysis for Upload Bridge application."""

    def __init__(self, app_root: Path):
        self.app_root = app_root
        self.results = {}
        self.measurements = {}

    def measure_startup_time(self) -> Dict[str, float]:
        """Measure application startup time with detailed breakdown."""
        print("🚀 Measuring application startup performance...")

        startup_times = {}

        # Measure bootstrap loading
        start_time = time.perf_counter()
        try:
            sys.path.insert(0, str(self.app_root))

            # Time bootstrap import
            bootstrap_start = time.perf_counter()
            import bootstrap
            bootstrap_time = time.perf_counter() - bootstrap_start
            startup_times['bootstrap_import'] = bootstrap_time

            # Time main module import
            main_start = time.perf_counter()
            import main
            main_time = time.perf_counter() - main_start
            startup_times['main_import'] = main_time

            # Time QApplication creation (if GUI)
            app_start = time.perf_counter()
            try:
                from PySide6.QtWidgets import QApplication
                import sys
                app = QApplication(sys.argv)
                app_time = time.perf_counter() - app_start
                startup_times['qapplication_init'] = app_time
            except ImportError:
                startup_times['qapplication_init'] = 0.0

            total_startup = time.perf_counter() - start_time
            startup_times['total_startup'] = total_startup

        except Exception as e:
            print(f"Warning: Could not complete startup measurement: {e}")
            startup_times['total_startup'] = time.perf_counter() - start_time

        return startup_times

    def profile_imports(self) -> Dict[str, Any]:
        """Profile import performance using cProfile."""
        print("📊 Profiling import performance...")

        pr = cProfile.Profile()
        pr.enable()

        try:
            # Import the main application
            import sys
            sys.path.insert(0, str(self.app_root))

            import bootstrap
            import main

            # Try to import core modules
            import core.pattern
            import core.config
            import ui.main_window

        except Exception as e:
            print(f"Warning: Import profiling incomplete: {e}")

        pr.disable()

        # Analyze profile results
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 time-consuming functions

        return {
            'profile_output': s.getvalue(),
            'stats': ps.stats
        }

    def analyze_memory_usage(self) -> Dict[str, Any]:
        """Analyze memory usage during startup."""
        print("💾 Analyzing memory usage...")

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_points = {}

        try:
            # Memory after bootstrap
            sys.path.insert(0, str(self.app_root))
            import bootstrap
            memory_points['after_bootstrap'] = process.memory_info().rss / 1024 / 1024

            # Memory after main import
            import main
            memory_points['after_main'] = process.memory_info().rss / 1024 / 1024

            # Memory after core imports
            import core.pattern
            import core.config
            memory_points['after_core'] = process.memory_info().rss / 1024 / 1024

            # Memory after UI imports (if available)
            try:
                import ui.main_window
                memory_points['after_ui'] = process.memory_info().rss / 1024 / 1024
            except ImportError:
                memory_points['after_ui'] = memory_points['after_core']

        except Exception as e:
            print(f"Warning: Memory analysis incomplete: {e}")

        memory_points['initial'] = initial_memory
        memory_points['peak'] = max(memory_points.values())

        return memory_points

    def analyze_lazy_loading(self) -> Dict[str, Any]:
        """Analyze which modules support lazy loading."""
        print("🔄 Analyzing lazy loading opportunities...")

        lazy_analysis = {
            'immediate_imports': [],
            'lazy_candidates': [],
            'import_warnings': []
        }

        # Check main.py for immediate imports
        main_file = self.app_root / 'main.py'
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()

            # Look for imports at module level
            lines = content.split('\n')
            for i, line in enumerate(lines[:50]):  # Check first 50 lines
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    lazy_analysis['immediate_imports'].append(f"main.py:{i+1}: {line}")

        # Check for heavy imports that could be lazy
        heavy_modules = [
            'PySide6.QtWidgets',
            'PySide6.QtGui',
            'PySide6.QtCore',
            'opencv-python',
            'PIL',
            'numpy'
        ]

        for module in heavy_modules:
            if f"import {module}" in content or f"from {module}" in content:
                lazy_analysis['lazy_candidates'].append(module)

        return lazy_analysis

    def generate_optimization_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate specific optimization recommendations based on results."""
        recommendations = []

        startup_times = results.get('startup_times', {})
        memory_usage = results.get('memory_usage', {})
        lazy_analysis = results.get('lazy_analysis', {})

        # Startup time recommendations
        total_startup = startup_times.get('total_startup', 0)
        if total_startup > 3.0:
            recommendations.append("⚠️  SLOW STARTUP: Total startup time > 3s. Consider lazy loading heavy modules.")
        elif total_startup > 1.0:
            recommendations.append("ℹ️  MODERATE STARTUP: Startup time > 1s. Minor optimizations possible.")

        bootstrap_time = startup_times.get('bootstrap_import', 0)
        if bootstrap_time > 0.5:
            recommendations.append("🔧 Bootstrap import is slow. Review bootstrap.py for optimization opportunities.")

        # Memory recommendations
        peak_memory = memory_usage.get('peak', 0)
        if peak_memory > 200:  # MB
            recommendations.append("💾 HIGH MEMORY: Peak usage > 200MB. Consider reducing import scope.")

        # Lazy loading recommendations
        lazy_candidates = lazy_analysis.get('lazy_candidates', [])
        if lazy_candidates:
            recommendations.append(f"🔄 LAZY LOADING: Consider deferring imports of: {', '.join(lazy_candidates[:3])}")

        immediate_imports = lazy_analysis.get('immediate_imports', [])
        if len(immediate_imports) > 10:
            recommendations.append("📦 TOO MANY IMPORTS: Consider reducing immediate imports in main.py")

        # General recommendations
        recommendations.extend([
            "✅ GOOD: No critical performance issues detected",
            "🔧 TIP: Use 'importlib' for conditional imports when possible",
            "💡 TIP: Consider using __import__ for rarely used heavy modules"
        ])

        return recommendations

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete performance analysis."""
        print("🔬 Running comprehensive performance analysis...")

        results = {}

        # Measure startup performance
        results['startup_times'] = self.measure_startup_time()

        # Profile imports
        results['import_profile'] = self.profile_imports()

        # Analyze memory usage
        results['memory_usage'] = self.analyze_memory_usage()

        # Analyze lazy loading opportunities
        results['lazy_analysis'] = self.analyze_lazy_loading()

        # Generate recommendations
        results['recommendations'] = self.generate_optimization_recommendations(results)

        return results

    def print_report(self, results: Dict[str, Any]):
        """Print formatted performance report."""
        print("\n" + "="*60)
        print("📈 UPLOAD BRIDGE PERFORMANCE REPORT")
        print("="*60)

        # Startup times
        startup_times = results.get('startup_times', {})
        print("\n🚀 STARTUP PERFORMANCE:")
        for key, value in startup_times.items():
            print(".3f")

        # Memory usage
        memory_usage = results.get('memory_usage', {})
        print("\n💾 MEMORY USAGE:")
        for key, value in memory_usage.items():
            print(".1f")

        # Lazy loading analysis
        lazy_analysis = results.get('lazy_analysis', {})
        immediate_imports = lazy_analysis.get('immediate_imports', [])
        lazy_candidates = lazy_analysis.get('lazy_candidates', [])

        print("\n🔄 IMPORT ANALYSIS:")
        print(f"   Immediate imports: {len(immediate_imports)}")
        print(f"   Lazy loading candidates: {len(lazy_candidates)}")

        if lazy_candidates:
            print(f"   Candidates: {', '.join(lazy_candidates[:5])}")

        # Top profile results
        import_profile = results.get('import_profile', {})
        profile_output = import_profile.get('profile_output', '')
        if profile_output:
            print("\n📊 TOP IMPORT FUNCTIONS:")
            # Show first few lines of profile
            lines = profile_output.split('\n')[:15]
            for line in lines:
                if line.strip():
                    print(f"   {line}")

        # Recommendations
        recommendations = results.get('recommendations', [])
        print("\n💡 RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"   {rec}")

        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="Performance profiler for Upload Bridge")
    parser.add_argument("--profile-startup", action="store_true", help="Profile startup performance")
    parser.add_argument("--analyze-imports", action="store_true", help="Analyze import performance")
    parser.add_argument("--generate-report", action="store_true", help="Generate full performance report")
    parser.add_argument("--root", default=".", help="Application root directory")

    args = parser.parse_args()

    app_root = Path(args.root).resolve()

    if not app_root.exists():
        print(f"Error: Root path {app_root} does not exist")
        return 1

    profiler = PerformanceProfiler(app_root)

    if args.generate_report or (not args.profile_startup and not args.analyze_imports):
        # Run full analysis
        results = profiler.run_full_analysis()
        profiler.print_report(results)
    else:
        results = {}

        if args.profile_startup:
            results['startup_times'] = profiler.measure_startup_time()
            print("Startup times:", results['startup_times'])

        if args.analyze_imports:
            results['import_profile'] = profiler.profile_imports()
            print("Import profile generated")

    return 0


if __name__ == "__main__":
    sys.exit(main())
