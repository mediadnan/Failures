import pytest

from failures import plugins  # noqa


@pytest.mark.parametrize(
    "name,matches", [
        ("failures_handler_logging", True),
        ("failures-handler-logging", True),
        ("failures-handler_logging", False),
        ("failures_handler-logging", False),
        ("failureshandlerlogging", False),
    ]
)
def test_plugin_name_pattern(name: str, matches: bool):
    match = plugins.PluginNamePattern.match(name)
    assert bool(match) is matches, "pattern didn't match and should" if matches else "pattern matches and shouldn't"
    if matches:
        assert match.group('name') == "logging", "didn't pick the right name"


class Module:
    def __init__(self, **attrs):
        self.__dict__.update(attrs)


def test_loading_plugins_without(monkeypatch):
    import pkgutil
    import importlib
    _modules = {'loggings': Module(), 'requests': Module(), 'failures': Module()}
    monkeypatch.setattr(pkgutil, 'iter_modules', lambda *args, **kwargs: ((object(), name, True) for name in _modules))
    monkeypatch.setattr(importlib, 'import_module', lambda name: _modules[name])
    handlers = {}
    default_handler = plugins.load_plugin_handlers(handlers)
    assert default_handler is None
    assert handlers == {}


def test_loading_plugins_with_plugins(monkeypatch):
    import pkgutil
    import importlib
    _handlers = {
        'log': lambda src, err: None,
        'print': lambda src, err: None,
        'logging': lambda src, err: None,
        'report': lambda src, err: None,
    }
    _modules = {'failures': Module(),
                'failures_log': Module(handler=_handlers['log']),
                'failures_handler_print': Module(handler=_handlers['print']),
                'failures_handler_logging': Module(handler=_handlers['logging']),
                'failures_handler_report': Module(failure_handler=_handlers['report']),
                'failures_handler_no_handler': Module()}
    monkeypatch.setattr(pkgutil, 'iter_modules', lambda *args, **kwargs: ((object(), name, True) for name in _modules))
    monkeypatch.setattr(importlib, 'import_module', lambda name: _modules[name])
    handlers = {}
    default_handler = plugins.load_plugin_handlers(handlers)
    assert default_handler is _handlers['print']    # first one found
    assert handlers == {'print': _handlers['print'], 'logging': _handlers['logging']}
