# Benchmark results
Code block was executed in the interpreter (``windows11 x64, 32.0GB RAM, AMD Ryzen 7 2700 8Core 3.20 GHz``) to compare 
between ``py``, ``py -O`` and ``py -OO`` normal and optimized modes, named respectively ``NORMAL``, ``OPTIMIZED`` and 
``DOUBLE_OPTIMIZED``.

## Reporter recursive creation
Comparing the recursive reporter creation between modes running this code:
````pycon
>>> from timeit import timeit
>>> from failures import Reporter
>>> timeit(lambda: Reporter("name")("name")("name")("name"))
````

Comparison

+--------------------+--------------------+--------------------+
|     ``NORMAL``     |    ``OPTIMIZED``   |``DOUBLE_OPTIMIZED``|
+--------------------+--------------------+--------------------+
|       ``1``        |``0.44097825039613``|``0.43995090021065``|
+--------------------+--------------------+--------------------+
