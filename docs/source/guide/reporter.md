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

## Failures
TODO / define the failure

## Creating a reporter

TODO / name conventions
TODO / calling report()

## Sub reporters

TODO / created sub reporter
TODO / creating sub, sub reporter
TODO / comparing nodes' API (name, parent, root, label)
TODO / calling report() from each
TODO / accessing failures from each

## Operation severities

TODO / Severity definition
TODO / Override normal severity
TODO / calling report() for each case

## Safe context

TODO / Safe function wrapper shorthand
TODO / Async support
