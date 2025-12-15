"""Tests for example scripts and notebooks.

These tests actually execute the examples to verify they work.
"""

import subprocess
import sys


class TestPythonExamples:
    """Test that Python example scripts execute without errors."""

    def test_basic_api_runs(self):
        """basic_api.py executes without errors (server not required - will fail gracefully)."""
        # The script will fail to connect but should not have import/syntax errors
        result = subprocess.run(
            [sys.executable, "examples/basic_api.py"],
            capture_output=True,
            timeout=10,
        )
        # Either exits 0 (server running) or fails with connection error (not import error)
        stderr = result.stderr.decode()
        if result.returncode != 0:
            # Should fail due to connection refused, not import error
            assert "ModuleNotFoundError" not in stderr, f"Missing module: {stderr}"
            assert "ImportError" not in stderr, f"Import error: {stderr}"
            assert "SyntaxError" not in stderr, f"Syntax error: {stderr}"

    def test_advanced_api_runs(self):
        """advanced_api.py executes without errors (server not required - will fail gracefully)."""
        result = subprocess.run(
            [sys.executable, "examples/advanced_api.py"],
            capture_output=True,
            timeout=60,  # Advanced example makes many API calls
        )
        stderr = result.stderr.decode()
        if result.returncode != 0:
            assert "ModuleNotFoundError" not in stderr, f"Missing module: {stderr}"
            assert "ImportError" not in stderr, f"Import error: {stderr}"
            assert "SyntaxError" not in stderr, f"Syntax error: {stderr}"


class TestNotebooks:
    """Test that Jupyter notebooks execute without errors."""

    def test_spectral_analysis_executes(self):
        """spectral_analysis.ipynb executes all cells without errors."""
        result = subprocess.run(
            [
                sys.executable, "-m", "jupyter", "nbconvert",
                "--to", "notebook",
                "--execute",
                "--ExecutePreprocessor.timeout=60",
                "--output", "/tmp/spectral_analysis_out.ipynb",
                "examples/spectral_analysis.ipynb",
            ],
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode()
            stdout = result.stdout.decode()
            raise AssertionError(f"Notebook execution failed:\n{stderr}\n{stdout}")

    def test_cospectral_exploration_executes(self):
        """cospectral_exploration.ipynb executes all cells without errors."""
        result = subprocess.run(
            [
                sys.executable, "-m", "jupyter", "nbconvert",
                "--to", "notebook",
                "--execute",
                "--ExecutePreprocessor.timeout=60",
                "--output", "/tmp/cospectral_exploration_out.ipynb",
                "examples/cospectral_exploration.ipynb",
            ],
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode()
            stdout = result.stdout.decode()
            raise AssertionError(f"Notebook execution failed:\n{stderr}\n{stdout}")
