# Changelog

All notable changes to this project will be documented in this file.

The format is based on <a href="https://keepachangelog.com/en/1.0.0/" target="_blank">Keep a Changelog <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/arrow-up-right-from-square.svg" width="16" height="16"/></a>,
and this project adheres to <a href="https://semver.org/spec/v2.0.0.html" target="_blank">Semantic Versioning <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/arrow-up-right-from-square.svg" width="16" height="16"/></a>.

# [1.0.0] - 2023-05-07
The library was refactored and improved drastically with more functionality and better design, the previous version,
however, is not supported and no longer maintained, and almost everything is a breaking change.

This section highlights the most remarkable changes;

### Added
- The ``Reporter`` used to gather failures between functions and reports them,  
  it is also used to execute functions _(normal or async)_ in an isolated environment to automatically capture errors.
- The ``Failure`` named tuple to encapsulate failure information.
- The ``FailureException`` is custom exception that stops the execution and sends failure information to the outer layer scope or handler.
- The ``@scoped`` decorator that automatically labels the function's scope with its name or a custom name and processes the passed reporter,
  supports both normal and asynchronous functions.
- The ``Handler`` object used to capture and process failures either ``FailureException`` or ``Failure`` from the reporter,
  it supports multiple handler functions and conditional handlers that only targets a specific group of failures. 
- The ``print_failure`` is a default handler that prints the failure information as log with a date to the standard output. 
- The ``Not`` utility used to counteract a filter or filters.
- Full library documentation using ``sphinx`` and ``myst_parser``.

### Changed
- All internal and external API was changed between version ``0`` and version ``1``.

### Removed
- Dropped plugin support for third party failure handlers, they can be directly implemented by the user.
- ``handle`` in favor of ``Handler`` with much more functionality.
- ``scope`` and ``Scoped`` in favor of a more sophisticated failure reporter ``Reporter``.

## [0.1.0] - 2023-04-04
First release.