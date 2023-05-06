import re
import sys
import importlib
from unittest.mock import patch
import pytest

from failures import print_failure, Failure


@pytest.fixture
def failure(error):
    return Failure("root.target", error, {})


def test_print_failure(capsys, failure):
    print_failure(failure)
    assert re.match(r".*\[FAILURE].*root\.target.*::.*Exception\(.*Test error.*\).*\d{4}-\d\d-\d\d \d\d:\d\d:\d\d.*",
                    capsys.readouterr().out)


def test_print_failure_without_colorama(capsys, failure):
    import failures
    with patch.dict(sys.modules, {'colorama': None}):
        importlib.reload(failures.handler)
        failures.print_failure(failure)
        assert re.match(r"\[FAILURE] root\.target :: Exception\(Test error\) \d{4}-\d\d-\d\d \d\d:\d\d:\d\d",
                        capsys.readouterr().out)
    importlib.reload(failures.handler)
