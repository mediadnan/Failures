import re
import sys
import importlib
from unittest.mock import patch
import pytest

import failures


def test_print_failure(capsys):
    failures.print_failure("root.target", ValueError("test error"))
    assert re.match(r".*\[FAILURE].*root\.target.*::.*ValueError\(.*test error.*\).*\d{4}-\d\d-\d\d \d\d:\d\d:\d\d.*",
                    capsys.readouterr().out)


def test_print_failure_without_colorama(capsys):
    with patch.dict(sys.modules, {'colorama': None}):
        importlib.reload(failures._print)
        failures.print_failure("root.target", ValueError("test error"))
        assert re.match(r"\[FAILURE] root\.target :: ValueError\(test error\) \d{4}-\d\d-\d\d \d\d:\d\d:\d\d",
                        capsys.readouterr().out)
    importlib.reload(failures._print)


@pytest.mark.parametrize("context", ["failures.handle('test')", "failures.scope('test', failures.print_failure)"])
def test_integration_with_failures(capsys, context):
    # ensures compatibility with v0.1
    with eval(context):
        with failures.scope("sub"):
            raise Exception("test error")
    assert re.match(
        r".*\[FAILURE].*test\.sub.*::.*Exception\(.*test error.*\).*\d{4}-\d\d-\d\d \d\d:\d\d:\d\d.*",
        capsys.readouterr().out
    )
