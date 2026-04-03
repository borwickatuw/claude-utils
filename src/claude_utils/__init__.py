"""claude-utils: Utilities for managing Claude Code local data."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("claude-utils")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
