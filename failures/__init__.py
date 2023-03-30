"""
This small package provides context managers tools to handle nested errors and report them pinpointing their location.
"""
from contextlib import suppress     # noqa: F401
from .context import scope, handle

__version__ = "0.1.0-alpha.1"
