"""Initialize system library paths for WeasyPrint.

This module MUST be imported BEFORE importing weasyprint to ensure
dynamic library loading works correctly across different operating systems.

macOS: Sets DYLD_LIBRARY_PATH to include Homebrew library paths
Linux: Libraries are typically found via system paths (apt/dnf packages)
"""

import os
import platform
import subprocess


def _setup_macos_library_paths() -> None:
    """Configure library paths for macOS (Homebrew)."""
    # Check if we're on macOS
    if platform.system() != "Darwin":
        return

    # Try to get Homebrew prefix
    homebrew_prefix = None

    # Check common Homebrew locations
    if os.path.exists("/opt/homebrew/lib"):  # Apple Silicon
        homebrew_prefix = "/opt/homebrew"
    elif os.path.exists("/usr/local/lib"):  # Intel Mac
        homebrew_prefix = "/usr/local"
    else:
        # Try to get prefix from brew command
        try:
            result = subprocess.run(
                ["brew", "--prefix"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                homebrew_prefix = result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    if homebrew_prefix:
        lib_path = f"{homebrew_prefix}/lib"
        current_path = os.environ.get("DYLD_LIBRARY_PATH", "")

        if lib_path not in current_path:
            new_path = f"{lib_path}:{current_path}" if current_path else lib_path
            os.environ["DYLD_LIBRARY_PATH"] = new_path


# Initialize on module import
_setup_macos_library_paths()
