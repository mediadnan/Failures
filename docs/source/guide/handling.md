(handling)=
# Handling failures
Collecting failures related to an application action is only done
to process and analyze them later, then take some action based on that.

How to handle failures however, is totally up to you _(the user)_ and depends on the failure type
and the application logic, ``failures`` just provides tools to help process them easily.

## Failure handling function
In simple terms, a failure handler is just a function _(or callable in general)_ that takes a {class}`failures.Failure`
object as the only _(positional)_ argument and is expected to return nothing.
In other words, it should have this signature ``(Failure) -> None``.

Async functions are not yet supported by ``failures`` as handlers, if required, the user must prepare and store failures
as an intermediate action then do some asynchronous action implemented by the user.

By default, and as a placeholder handler, ``failures`` comes with {func}``failures.print_failure``
that prints the failure to the standard output with the date it was registered.

````pycon
>>> from failures import Reporter, print_failure
>>> reporter = Reporter('testing_default_handler')
>>> reporter.report(Exception("Generic error"))
>>> failure = reporter.failures[0]
>>> print_failure(failure)
[FAILURE] testing_default_handler :: Exception(Generic error) 2023-04-30 20:00:00
````

We can implement our own handler
````pycon
>>> from logging import getLogger, basicConfig
>>> from failures import Reporter, Failure
>>> basicConfig(format="%(name)s: %(message)s [%(asctime)s]")
>>> def handler(failure: Failure) -> None:
        source, error, details = failure
...     getLogger(source).error(f"{error = !r} {details = !r}")
>>> reporter = Reporter('testing_default_handler')
>>> reporter.report(Exception("Generic error"), input=22)
>>> handler(reporter.failures[0])
testing_default_handler: error = Exception('Generic error') details = {'input': 22} [2023-04-30 20:00:00,399]
````

The failure object failure can be interpreted as tuple or as object, so the failure's source can be accessed 
like ```failure.source``` or like ``failure[0]``, the same for error, either ``failure.error`` or ``failure[1]`` ...

## Handler
For more complex use-cases, like filtering and choosing which failures to handle and which function to use for each,
a function as handler can become a bit harder to maintain.

Meanwhile, The {class}`failures.Handler` object can be used as failure handler, the object is a callable just like
a regular function, it has the ``(Failure) -> None`` signature, but this handler has some additional features that
we're going to discover.

The {class}`failures.Handler` can be used to combine and organize multiple handler function together, and create
conditional handlers that are called only for a targeted type of failures, it can also be used as a context manager
to capture and handle failure exceptions raised by reporters for required operations, and last but not least
it can handle failures directly from the reporter using the {meth}`failures.Handler.from_reporter`.

The constructor ``Handler()`` when called without arguments, it takes {func}`failures.print_failure` as the default
handler, this is useful when testing code directly in the interpreter.

However, the constructor takes one or many arguments, they can be functions that handle failures, or more specific 
structures that we are going to discover later in this chapter.

A quick example of using the {class}`failures.Handler`

````pycon
>>> from failures import Failure, Handler
>>> failure = Failure('reporter_name', Exception('test error'), {})
>>> registry: list[Failure] = []
>>> handler = Handler(print, registry.append)
>>> handler(failure)    # handle failure
Failure(source='reporter_name', error=Exception('test error'), details={})
>>> registry
[Failure(source='reporter_name', error=Exception('test error'), details={})]
>>> # Handler with default handler
>>> handler2 = Handler()
>>> handler2(failure)
[FAILURE] reporter_name :: Exception(test error) 2023-05-02 08:00:00
````

Automatically iterating and processing failures from {class}`failures.Reporter`

````pycon
>>> from failures import Reporter, Handler
>>> reporter = Reporter('testing_handler')
>>> def fail(msg: str):
...     raise Exception(msg)
...
>>> with Handler(print) as handler:
...     reporter.safe(fail, "error 1")
...     reporter.safe(fail, "error 2")
...     reporter.required(fail, "error 3")  # this is the last step
...     reporter.safe(fail, "will never be registered")
...
Failure(source='testing_handler', error=Exception('error 3'), details={})
>>> handler.from_reporter(reporter)
Failure(source='testing_handler', error=Exception('error 1'), details={})
Failure(source='testing_handler', error=Exception('error 2'), details={})
````

As we mentioned, the handler can specify failure handler functions that only apply to a specific group of failures,
in the following sections we will see how to filter failures.

````{Important}
Handler objects should be created _(defined)_ once through the application lifetime and not each time they need
to be called, they are not _very_ optimized to be used that way like reporters are, as multiple operations
and valdations are performed.
````

## Conditional handlers
Handlers can target only a specific group of failures, we can make different handlers for different groups of failures,
and this is done by specifying a filter together with the handler when creating the {class}`failures.Handler` object.

Failures can be filtered by source label or by exception type, so, a conditional handler is specified by passing a tuple
of the handler function with the filter to ``Handler(...)``, and the syntax is ``Handler((func, filter), ...)``.
The ``filter`` is either a string targeting a label or a group of labels, an exception type that targets
a specific error type to handle _(like ``KeyError``, ``ValueError``, ...)_, or a mixture of both.

### Filter by label
If we want a handler ``func`` to target a specific failure by its label ``'rep.label'``, we pass a tuple of 
``(func, 'rep.label')`` to {class}`failures.Handler` when creating the handler, like ``Handler((func, 'rep.label'))``
instead of ``Handler(func)``, this makes the handler call the function for failures with that specific label and ignore
the rest.

Let's test this 
````pycon
>>> from failures import Reporter, Handler
>>> # Creating a tiny reporter tree
>>> root = Reporter("root")
>>> proc1 = root("process1")
>>> proc2 = root("process2")
>>> # Reporting errors
>>> root.report(Exception("from root"))
>>> proc1.report(Exception("from proc1"))
>>> proc2.report(Exception("from proc2"))
>>> # Checking reported failures
>>> for _failure in root.failures:
...     print(failure)
...     
Failure(source='root', error=Exception('from root'), details={})
Failure(source='root.process1', error=Exception('from proc1'), details={})
Failure(source='root.process2', error=Exception('from proc2'), details={})
>>> # Implementing the handler
>>> def custom(failure):
...     print(f"(*)custom failure => source: {failure.source}, error: {failure.error!r}")
...
>>> Handler((custom, "root.process1"), print).from_reporter(root)
Failure(source='root', error=Exception('from root'), details={})
(*)custom failure => source: root.process1, error: Exception('from proc1')
Failure(source='root.process1', error=Exception('from proc1'), details={})
Failure(source='root.process2', error=Exception('from proc2'), details={})
````

As shown in this example, ``print()`` was called with all reported failures, but ``custom()`` was only called for
the failure labeled exactly ``'root.process1'``. 
This can be useful to control which function handles which failure, but implementing a handler to handle one single 
failure is rarely the desired behaviour, we can target a group of labels using the wildcard symbol ``*``.

If we want to process all failures under ``'root'`` label but not ``'root'`` itself, we can filter by ``"root.*"``

````pycon
...
>>> Handler((custom, "root.*")).from_reporter(root)
(*)custom failure => source: root.process1, error: Exception('from proc1')
(*)custom failure => source: root.process2, error: Exception('from proc2')
````

The wildcard symbol ``*`` matches everything, and it can be placed anywhere it's needed

````pycon
...
>>> Handler((custom, "*process*")).from_reporter(root)
(*)custom failure => source: root.process1, error: Exception('from proc1')
(*)custom failure => source: root.process2, error: Exception('from proc2')
````

````{note}
This instruction ``Handler((handle, '*'))`` is the same as this one ``Handler(handle)``, as `'*'` matches everything.
````

### Filter by error type
We've seen how to filter failures by their label, but we can also filter by exception type to target only a type of 
errors and it subclasses.

To create a conditional handler ``func`` that only targets failures with specific error type ``SomeError``,
we pass a tuple of ``(func, SomeError)`` to the constructor, if this is the only handler passed to it, the handler
will only handle failures caused by ``SomeError`` and ignore the rest.

````pycon
>>> from failures import Handler, Reporter
>>> reg = []
>>> handler = Handler(
...     ((lambda f: print(f"(handler 2) >>>> {f!r}")), ValueError),
...     ((lambda f: print(f"[handler 1]  ::  {f!r}")), [KeyError, IndexError]),
...     reg.append
... )
>>> reporter = Reporter("filtering_by_exctype")
>>> for ErrType in (KeyError, IndexError, ValueError, TypeError, NameError, RecursionError):
...     reporter.report(ErrType("test err"))
... 
>>> handler.from_reporter(reporter)
[handler 1]  ::  Failure(source='filtering_by_exctype', error=KeyError('test err'), details={})
[handler 1]  ::  Failure(source='filtering_by_exctype', error=IndexError('test err'), details={})
(handler 2) >>>> Failure(source='filtering_by_exctype', error=ValueError('test err'), details={})
>>> from pprint import pp
... pp(reg)
[Failure(source='filtering_by_exctype', error=KeyError('test err'), details={}),
 Failure(source='filtering_by_exctype', error=IndexError('test err'), details={}),
 Failure(source='filtering_by_exctype', error=ValueError('test err'), details={}),
 Failure(source='filtering_by_exctype', error=TypeError('test err'), details={}),
 Failure(source='filtering_by_exctype', error=NameError('test err'), details={}),
 Failure(source='filtering_by_exctype', error=RecursionError('test err'), details={})]
````

We defined this handler with three handler functions, the first two are conditional and the last one is not,
the first handler is only called if the error type is ``ValueError`` or its subclass, the second is called if the type
of the error is **either ``KeyError`` or ``IndexError``**.
The last handler is called for every failure, it stores the failure as it is in a predefined list.

````{note}
This instruction ``Handler((handle, Exception))`` is the same as this one ``Handler(handle)``, 
as `Exception` matches everything that can be handled.
````

### Combining filters
Filters can be as specific as we need them to be, we can combine multiple filters to match the specification:

Consider this list of failures

````pycon
>>> from failures import Handler, Failure
>>> failures = [
...     Failure("app.trigger", RuntimeError("..."), {}),
...     Failure("client.data.download", TimeoutError("..."), {}),
...     Failure("client.data.process.decode", ValueError("..."), {}),
...     Failure("client.data.process.extract", KeyError("..."), {}),
...     Failure("client.data.process.analyze", TypeError("..."), {}),
...     Failure("client.data.store", IOError("..."), {}),
...     Failure("app.notify", TypeError("..."), {}),
... ]
````

If we need to handle failures from ``data.process`` or failures with ``TypeError`` we can specify this by 
``(func, ['*.data.process*', TypeError])``, let test this

````pycon
...
>>> handler = Handler((print, ['*.data.process*', TypeError]))
>>> for failure in failures:
...     handler(failure)
... 
Failure(source='client.data.process.decode', error=ValueError('...'), details={})
Failure(source='client.data.process.extract', error=KeyError('...'), details={})
Failure(source='client.data.process.analyze', error=TypeError('...'), details={})
Failure(source='app.notify', error=TypeError('...'), details={})
````

Passing a list of filters results in a **union**  ![Venn-Diagram-Union](../../_static/diagrams/venn_union.svg){w=24px}
of conditions, it is compared like ``if (filter1 or filter2 or ...)``, if one condition is met then the handler will be
called.

But if we want to combine filters as an intersection ![Venn-Diagram-Intersection](../../_static/diagrams/venn_inter.svg){w=24px}
of conditions we have to use a tuple instead of a list

````pycon
...
>>> handler = Handler((print, ("client.*", TypeError)))
>>> for failure in failures:
...     handler(failure)
... 
Failure(source='client.data.process.analyze', error=TypeError('...'), details={})
````
This handler only processes failures with labels that start with ``'client'`` and errors of type
``TypeError``, it's like writing ``if (filter1 and filter2 and ...)``

We can combine as many conditions as we want using nested lists and tuples

````pycon
...
>>> handler = Handler((print, [("client.*", [KeyError, TypeError]), ("app.*", RuntimeError)]))
>>> for failure in failures:
...     handler(failure)
...
Failure(source='app.trigger', error=RuntimeError('...'), details={})
Failure(source='client.data.process.extract', error=KeyError('...'), details={})
Failure(source='client.data.process.analyze', error=TypeError('...'), details={})
````

### Exclusive filter
In case we need to specify a handler that handles every failure except a specific type, we can use {class}`failures.Not`,
it wraps a filter to inform the ``Handler`` that we mean the opposite.

Continuing with the previous example, if we want to handle everything but failures with ``process`` label or 
with ``TypeError`` errors, we can do this like the following

````pycon
... 
>>> from failures import Not
>>> handler = Handler((print, Not("*.process*", TypeError)))
>>> for failure in failures:
...     handler(failure)
...
Failure(source='app.trigger', error=RuntimeError('...'), details={})
Failure(source='client.data.download', error=TimeoutError('...'), details={})
Failure(source='client.data.store', error=OSError('...'), details={})
````
``Not`` can take one or multiple conditions, like ``Not('client.*')`` or like the previous example,
not that **multiple arguments are taken as a union**; so ``Not(ValueError, TypeError)`` is equivalent to 
``not isinstance(err, (ValueError, TypeError))`` or more specifically ``not (isinstance(err, ValueError) or isinstance(err, TypeError))``.

TODO: intersection

## Combining multiple handlers
We've seen how to combine multiple handler functions when we create a {class}`failures.Handler` by
placing them as positional arguments like ``Handler(func1, func2, ...)``, but what if we want to combine
multiple handlers that share the same filter; 

Is it ``Handler((func1, [filter1, filter2, ...]), (func2, [filter1, filter2, ...]), ...)``?

Of course not, there is a better way to combine handlers with common filters, the syntax is ``((func1, func2), [filter1, filter2, ...])``,
by wrapping those functions within a tuple as first member a conditional handler tuple.

Now let's continue with the previous example and add a registry list

````pycon
... 
>>> registry = []
>>> handler = Handler(((print, registry.append), [("client.*", [KeyError, TypeError]), ("app.*", RuntimeError)]))
>>> for failure in failures:
...     handler(failure)
...
Failure(source='app.trigger', error=RuntimeError('...'), details={})
Failure(source='client.data.process.extract', error=KeyError('...'), details={})
Failure(source='client.data.process.analyze', error=TypeError('...'), details={})
>>> from pprint import pp
... pp(registry)
[Failure(source='app.trigger', error=RuntimeError('...'), details={}),
 Failure(source='client.data.process.extract', error=KeyError('...'), details={}),
 Failure(source='client.data.process.analyze', error=TypeError('...'), details={})]
````

The handlers are called in the same order they were inserted, ``print(failure)`` then ``registry.append(failure)``.
