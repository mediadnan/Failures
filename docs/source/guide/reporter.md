# Failures reporter
The reporter is a node object passed to functions that stores failures in a tree shared list, 
allowing them to be handled explicitly at the end of the function execution.

In production, functions with instructions that might fail, *like those that process inconsistent data*,
must be captured then reported and handled, such as writing failure logs and provide alternative code or value
when the failure is somehow expected or the processed value is not mandatory.
In scenarios like these, handling failures locally has two main problems: 

1. It is tedious, repetitive and error-prone. Imagine writing ``logging.error(...)`` all over the place,
   just to decide later adding or replacing the handling mechanism say ``requests.post("https://loggingserver.example.com/...", data=...)``,
   or maybe add a costume response HTTP for users in specific cases like ``raise HTTPException(404, "requested data not found")``...
   The solution for this problem is having the responsibility of handling failures separated from the processing function. 
2. The function is a reusable component, means that it should be used by multiple other functions to give a specific result.
   When the failure occurs, the function actually doesn't know its context unless explicitly digging in execution frames
   or following tracebacks, in either case, this can become unclear very quickly. As we know that error tracebacks 
   give us path-file-lineno information, it would be helpful to also pinpoint the **logical** location of the failure 
   like having a function named ``email_parsing`` but we need to know where exactly that function has failed, like
   ``app.user_registration.email_parsing``, ``app.user_login.email_parsing`` or ``app.notif.subscribers.email_parsing`` ...

The reporter object solves both those problems, as it's a named object and can pass its offsprings to functions as argument,
those sub reporters always keep reference of their parent reporter and can be used to hold failure information,
these failures are stored in a shared list that can be accessed through any of those reporters,
this way all failures can be handled after that the function has returned.

## Creating a reporter

The reporter is firstly created using ``failures.Reporter`` constructor that expects a name as mandatory positional-only argument,

````python
>>> from failures import Reporter
>>> reporter = Reporter('my_first_reporter')
>>> reporter
Reporter('my_first_reporter', NORMAL)
````

This reporter can be used now for storing failures:

````python
>>> reporter.report(ValueError("this is a value error"))
>>> reporter.report(TypeError("this is a type error"))
>>> reporter.report(KeyError("this is a key error"))
>>> for failure in reporter.failures:
...   print(failure)
Failure(source='my_first_reporter', error=ValueError('this is a value error'), details={}, severity=<Severity.NORMAL: 1>)
Failure(source='my_first_reporter', error=TypeError('this is a type error'), details={}, severity=<Severity.NORMAL: 1>)
Failure(source='my_first_reporter', error=KeyError('this is a key error'), details={}, severity=<Severity.NORMAL: 1>)
````

### Failures
As shown in the previous example, the reporter encapsulates errors in a **named tuple** object 
together with its _source_ _severity_ and optionally additional details as a dict.

The attributes can be either accesses as members ``failure.source`` or as items ``failure[0]``.

For more details, please refer to the {func}`failures.Failure` API reference

### Naming conventions
The name however must be a non-empty string, and can only contain letters, digits, ``-`` and ``_``,
like ``root``, ``evaluate_percentage``, ``func1``, ``get-item-price`` ...
And if for some reason the reporter needs multiple labels, this is allowed by joining those labels with dots,
like ``items.counter``. The name can also end with parenthesis or brackets containing those the previously mentioned
characters, like ``Iteration[64]``, ``branch[main]`` or ``Inbox(new)``.

The library will complain with **value errors** for invalid name patterns, such as ``items..counter``,
``branch[main)``, ``-toUpper``, ``(main branch)`` ...
This validation mechanism helps ensuring a good labeling quality, as this is a main features of this library.

## Sub reporters

We can derive a new reporter from an existing one the same way we create a new reporter,
this is achieved by calling the reporter with a new name like this

```python
>>> from failures import Reporter
>>> reporter = Reporter('main')
>>> sub_reporter = reporter('sub')
>>> sub_reporter
Reporter('main.sub', NORMAL)
```

We can keep deriving sub reporters as much as we need, like:

````python
>>> sub_sub = sub_reporter('sub')
>>> sub_sub
Reporter('main.sub.sub')
>>> sub_sub('sub_again')
Reporter('main.sub.sub.sub_again')
````
And this will help us when passing reporters to functions as arguments,
as they keep track of their origin. Making them the perfect tool to pinpoint
the source of the failure.

Now let's explore some common reporter properties and compare them

```python
>>> # reporter's label
>>> reporter.label
'main'
>>> sub_reporter.label
'main.sub'
>>> sub_sub.label
'main.sub.sub'
>>> # reporter's parent
>>> reporter.parent  # None

>>> sub_reporter.parent
Reporter('main', NORMAL)
>>> sub_sub.parent
Reporter('main.sub', NORMAL)
>>> # reporter's root
>>> reporter.root  # self
Reporter('main', NORMAL)
>>> sub_reporter.root
Reporter('main', NORMAL)
>>> sub_sub.root
Reporter('main', NORMAL)
>>> # reporter's name
>>> reporter.name
'main'
>>> sub_reporter.name
'sub'
>>> sub_sub.name
'sub'
```

As shown in this example, the ``label`` property gets the full combined tree names of the reporter, 
the ``name`` property only gets the current reporter's name, the ``parent`` property returns
the reporter's parent if there is one and the ``root`` property returns the first reporter
of the tree.

Reporters are made to report failures, and we can report from each report as they share the same failures' list,

````python
>>> reporter.report(TypeError('test type error'))
>>> sub_reporter.report(Exception('test generic error'))
>>> sub_sub.report(TabError('test error error'))
>>> reporter.failures

````

TODO / calling report() from each
TODO / accessing failures from each

## Operation severities

TODO / Severity definition
TODO / Override normal severity
TODO / calling report() for each case

## Safe context

TODO / Safe function wrapper shorthand
TODO / Async support
