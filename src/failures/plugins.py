import importlib
import pkgutil
import re
import typing as tp

from .core import FailureHandler


PluginNamePattern = re.compile(r'^failures(?P<sep>[_-])handler(?P=sep)(?P<name>.+)')


def load_plugin_handlers(_handlers: tp.Dict[str, FailureHandler]) -> tp.Optional[FailureHandler]:
    _default = None
    for finder, name, is_pkg in pkgutil.iter_modules():
        if not (plugin_func_name := PluginNamePattern.match(name)):
            continue
        module = importlib.import_module(name)
        if handler := vars(module).get('handler'):
            _handlers[plugin_func_name.group('name')] = handler
            if _default is None:
                _default = handler
    return _default


handlers: tp.Dict[str, FailureHandler] = {}
default_handler: tp.Optional[FailureHandler] = load_plugin_handlers(handlers)
