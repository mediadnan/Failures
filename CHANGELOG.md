# Changelog

All notable changes to this project will be documented in this file.

The format is based on <a href="https://keepachangelog.com/en/1.0.0/" target="_blank">Keep a Changelog <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/arrow-up-right-from-square.svg" width="16" height="16"/></a>,
and this project adheres to <a href="https://semver.org/spec/v2.0.0.html" target="_blank">Semantic Versioning <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/arrow-up-right-from-square.svg" width="16" height="16"/></a>.

## [unreleased]

### Added
- ``failure_handler`` optional _positional_ argument to ``Scope`` that holds a local failure handler.
- ``failures.handler`` a function that creates custom failure handler with ``ignore`` and ``propagate`` slots that filter failures.
- ```qualname``` property that returns a fully qualified _(dot separated)_ name of the ``failures.scope`` object.
- ``handle`` method to the ``Scope`` object that explicitly handle registered and given failures.
- ``failures.scoped`` decorator that wraps functions into a labeled failure scope.
- arbitrary keyword arguments the failure handler signature _(will be used to hold additional details)_

### Changed
- same scope label changed from **ValueError** exception to **UserWarning** warning.
- ``failures.scope`` internal implementation to make it suitable to be used as a context manager or as a node object.
- Changed ``failures`` from a single python module to a python package to better structure the project.
- **Mandatory** _(non-failure instance)_ error labeling to **optional** in ``Scope.add_failure``

### Deprecated
- Top level ``failures.handle`` in favor of ``failures.scope`` local handler.
- ```Failures.add``` method as it will not be used.
- ``SubScope`` Scope subclass helper class _(internal API)_.

## [0.1.0] - 2023-04-04
First stable release.