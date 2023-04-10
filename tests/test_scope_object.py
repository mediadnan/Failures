# ---------   Scope features test specifications    -------------------------------------#

#   Scope as context manager
#       * returns same scope object [IMPLEMENTED]
#       * catches exceptions and handles them automatically [IMPLEMENTED]
#       * does not catch BaseException above Exceptions [IMPLEMENTED]
#       * does not catch module validation errors [IMPLEMENTED]

#   Scope naming convention
#       * valid name testing [IMPLEMENTED]
#       * invalid name validation [IMPLEMENTED]

#   Derived scope
#       * name and dot separated qualname [IMPLEMENTED]
#       * duplicate sub name warning  [IMPLEMENTED]
#       * inherits parent handler by default [IMPLEMENTED]
#       * can override parent handler [IMPLEMENTED]

#   Scope failure handling
#       * coupled failure handling [IMPLEMENTED]
#       * decoupled failure handling [IMPLEMENTED]
#       * hybrid failure handling [IMPLEMENTED]
#       * manual failure gathering [IMPLEMENTED]
#           + invalid param validation [IMPLEMENTED]
#       * manual failure handling [IMPLEMENTED]
#           + does nothing if no failures are found [IMPLEMENTED]
#           + only error (as argument) handling [IMPLEMENTED]
#           + only registered failures handling [IMPLEMENTED]
#           + both error and registered failures handling [IMPLEMENTED]

# ---------------------------------------------------------------------------------------#

import typing
import pytest

import failures
from failures.core import Scope


# Scope as context manager
def test_scope_as_context_manager_self():
    scope = failures.scope('my_scope')
    with scope as context_scope:
        pass
    assert context_scope is scope, "expected the same scope object"


def test_scope_context_automatic_handler(handler, error):
    with failures.scope('test_scope', handler):
        raise error
    assert handler.failures == [('test_scope', error)], "error didn't get captured"


@pytest.mark.parametrize('ExceptionType', [BaseException, KeyboardInterrupt, GeneratorExit, SystemExit])
def test_scope_does_not_catch_higher_exceptions(ExceptionType, handler):
    with pytest.raises(ExceptionType):
        with failures.scope('test_scope', handler):
            raise ExceptionType("Testing exception")
    assert not handler.failures


@pytest.mark.parametrize('ExceptionType', [TypeError, ValueError, IndexError, Exception])
def test_scope_does_not_catch_validation_errors(ExceptionType, handler):
    with pytest.raises(ExceptionType):
        with failures.scope('test_scope', handler):
            raise failures.core._invalid(ExceptionType, "Testing exception")


# Scope naming convention
def test_valid_scope_labels(valid_label):
    assert failures.scope(valid_label)


def test_invalid_scope_labels(invalid_label, err_type, err_msg, handler):
    with pytest.raises(err_type, match=err_msg):
        failures.scope(invalid_label)


# Derived scope
@pytest.mark.parametrize("stem, name, qualname", [
    pytest.param("failures.scope('root')", "root", "root", id="root_scope"),
    pytest.param("failures.scope('root')('child')", "child", "root.child", id="scope_first_child"),
    pytest.param("failures.scope('root')('child')('sub')", "sub", "root.child.sub", id="scope_second_child"),
    pytest.param("failures.scope('root')('child')('sub')('sub_sub')", "sub_sub", "root.child.sub.sub_sub", id="scope_third_child"),
])
def test_scope_child_name_and_qualname(stem: str, name, qualname):
    scope: Scope = eval(stem)
    assert scope.name == name
    assert scope.qualname == qualname


def test_scope_child_inheriting_handler(handler):
    root_scope = failures.scope('root', handler)
    child_scope = root_scope('child')
    assert child_scope.handler is root_scope.handler


def test_scope_child_overrides_handler(handler):
    root_scope = failures.scope('root', handler)
    child_scope = root_scope('child', handler)
    assert child_scope.handler is not root_scope.handler


def test_duplicate_name_sub_scope():
    scope = failures.scope("root_scope")
    scope("sub_sub")
    with pytest.warns(Warning, match="'.*sub_sub' label has been used previously"):
        scope("sub_sub")


# Scope failure handling
def fail(error: Exception, scope: Scope = None):
    """raise the error for tests"""
    with (scope or failures.scope)('fail'):
        raise error


def coupled_failure_handling(error: Exception, scope: Scope):
    fail(error, scope('coupled'))


def decoupled_failure_handling(error: Exception):
    with failures.scope('decoupled'):
        fail(error)


def hybrid_multi_failure_handling(error: Exception, scope: Scope = None):
    with (scope or failures.scope)('hybrid') as scope:
        fail(error, scope('step[1]'))
        fail(error, scope('step[2]'))


@pytest.mark.parametrize("stem, sources", [
    pytest.param("coupled_failure_handling(error, _scope)", ['root.coupled.fail'], id="coupled"),
    pytest.param("decoupled_failure_handling(error)", ['root.decoupled.fail'], id="decoupled"),
    pytest.param("hybrid_multi_failure_handling(error, _scope)", ['root.hybrid.step[1].fail', 'root.hybrid.step[2].fail'], id="hybrid(coupled)"),
    pytest.param("hybrid_multi_failure_handling(error)", ['root.hybrid.step[1].fail', 'root.hybrid.step[2].fail'], id="hybrid(decoupled)"),
])
def test_failure_handling(stem: str, sources: typing.List[str], error, handler):
    with failures.scope('root', handler) as _scope:
        eval(stem)
    assert handler.sources == sources


def test_manual_error_gathering(handler, error):
    result = {}
    with failures.scope('root', handler) as scope:
        # Unlabeled failure added without label
        try:
            raise error
            result['first'] = object()  # noqa
        except Exception as err:
            scope.add_failure(err)
            result['first'] = None
        # Labeled failure added without label
        try:
            fail(error)
            result['second'] = object()  # noqa
        except Exception as err:
            scope.add_failure(err)
            result['second'] = None
        # Unlabeled failure added with label
        try:
            raise error
            result['third'] = object()  # noqa
        except Exception as err:
            scope.add_failure(err, 'labeled')
            result['third'] = None
        # Labeled failure added with label
        try:
            fail(error)
            result['fourth'] = object()  # noqa
        except Exception as err:
            scope.add_failure(err, 'labeled')
            result['fourth'] = None
        result['fifth'] = 'data'
    assert result['first'] is None, "alternative data for 'first' should be added"
    assert result['second'] is None, "alternative data for 'second' should be added"
    assert result['third'] is None, "alternative data for 'third' should be added"
    assert result['fourth'] is None, "alternative data for 'fourth' should be added"
    assert result['fifth'] == 'data', "last data should be added"
    assert handler.sources == ['root', 'root.fail', 'root.labeled', 'root.labeled.fail']


@pytest.mark.parametrize("handled", [True, False], ids=["handled", "unhandled"])
@pytest.mark.parametrize("failure, ExceptionType, err_msg", [
    pytest.param((object(),), TypeError, "invalid error type", id="wrong_failure_type"),
    pytest.param((object(), 'label'), TypeError, "invalid error type", id="wrong_failure_type_labeled"),
    pytest.param((Exception('test'), object()), TypeError, "label must be a string", id="wrong_label_type"),
    pytest.param((Exception('test'), ''), ValueError, "invalid label", id="wrong_label_value"),
])
def test_add_failure_validation(
        failure: tuple,
        ExceptionType: typing.Type[Exception],
        err_msg: str,
        handled: bool,
        handler
):
    with pytest.raises(ExceptionType, match=err_msg):
        with failures.scope('handler', handler if handled else None) as scope:
            scope.add_failure(*failure)  # noqa


def test_manual_handle_no_failures(handler, error):
    scope = failures.scope('root', handler)
    scope.handle()
    assert not handler.failures


@pytest.mark.parametrize('registered, expected_registered', [
    pytest.param('[]', [], id='nothing_registered'),
    pytest.param('[error]', ['root'], id='error_registered'),
    pytest.param('[Failure("label", error), error]', ['root.label', 'root'], id='failure_error_registered'),
    pytest.param('[Failures(Failure("label1", error), Failure("label2", error)), Failure("label", error), error]', [
        'root.label1',
        'root.label2',
        'root.label',
        'root'
    ], id='failures_failure_error_registered'),
])
@pytest.mark.parametrize('passed, expected_passed', [
    pytest.param('None', [], id='nothing_passed'),
    pytest.param('error', ['root'], id='error_passed'),
    pytest.param('Failure("label", error)', ['root.label'], id='failure_passed'),
    pytest.param('Failures(Failure("label1", error), Failure("label2", error))', [
        'root.label1', 'root.label2'
    ], id='failures_passed'),
])
def test_manual_handle_given_failure(handler, error, passed: str, registered: str, expected_passed, expected_registered):
    from failures.core import Failures, Failure  # noqa (available for failure source)
    scope = failures.scope('root', handler)
    for failure in eval(registered):
        scope.add_failure(failure)
    scope.handle(eval(passed))
    assert handler.sources == [*expected_registered, *expected_passed]
