import importlib
import pkgutil
import re
from typing import Protocol, Dict, Optional

__all__ = ("FailureHandler", "handlers", "default_handler")


# signature of a failure handler function
class FailureHandler(Protocol):
    def __call__(self, source: str, error: Exception):
        """Takes two positional arguments; the source of failure and the error that caused it"""


handlers: Dict[str, FailureHandler] = {}
default_handler: Optional[FailureHandler] = None

PluginNamePattern = re.compile(r'^failures(?P<sep>[_-])handler(?P=sep)(?P<name>.+)')

for finder, name, is_pkg in pkgutil.iter_modules():
    if not (plugin_func_name := PluginNamePattern.match(name)):
        continue
    module = importlib.import_module(name)
    if handler := vars(module).get('handler'):
        global handlers, default_handler
        handlers[plugin_func_name.group('name')] = handler
        if default_handler is None:
            default_handler = handler
