# multiprocessing-logging

[![Supported Python versions](https://img.shields.io/pypi/pyversions/multiprocessing-logging.svg)](https://pypi.python.org/pypi/multiprocessing-logging/)
[![License](https://img.shields.io/pypi/l/multiprocessing-logging.svg)](https://pypi.python.org/pypi/multiprocessing-logging/)


When using the `multiprocessing` module, logging becomes less useful since
sub-processes should log to individual files/streams or there's the risk of
records becoming garbled.

This simple module implements a `Handler` that when set on the root
`Logger` will handle tunneling the records to the main process so that
they are handled correctly.

It's currently tested in Linux and Python 2.7 & 3.6+.

Pypy3 hangs on the tests so I don't recommend using it.

Pypy appears to be working, recently.

Only works on POSIX systems and only Linux is supported. It does not work on Windows.

# Origin

This library was taken verbatim from a [StackOverflow post](http://stackoverflow.com/questions/641420/how-should-i-log-while-using-multiprocessing-in-python)
and extracted into a module so that I wouldn't have to copy the code in every
project.

Later, several improvements have been contributed.

# Usage

Before you start logging but after you configure the logging framework (maybe with `logging.basicConfig(...)`), do the following:

```py
import multiprocessing_logging

multiprocessing_logging.install_mp_handler()
```

and that's it.

## With multiprocessing.Pool

When using a Pool, make sure `install_mp_handler` is called before the Pool is instantiated, for example:

```py
import logging
from multiprocessing import Pool
from multiprocessing_logging import install_mp_handler

logging.basicConfig(...)
install_mp_handler()
pool = Pool(...)
```

Rules of the thumb when setting up `multiprocess_logging`

- Call `install_mp_handler()` only in the main process, not in individual subprocesses.
- Depending on when subprocesses fork you need to configure logging formats and levels in the subprocesses.
  This may or may not include `logger.setLevel()` or `logger.setFormatter()`. However `install_mp_hander()`
  should be only called in the main process, or you will get resource leaks.

# Problems
The approach of this module relies on
[fork](https://docs.python.org/3.9/library/multiprocessing.html#multiprocessing.set_start_method)
being used to create new processes. This start method
[is basically unsafe when also using threads](https://bugs.python.org/issue37429),
as this module does.

The consequence is that there's a low probability of the application hanging
when creating new processes.

As a palliative, don't continuously create new processes. Instead, create a
Pool once and reuse it.
