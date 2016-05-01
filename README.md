# multiprocessing-logging

[![Downloads](https://pypip.in/download/multiprocessing-logging/badge.svg)](https://pypi.python.org/pypi/multiprocessing-logging/)
[![Supported Python versions](https://pypip.in/py_versions/multiprocessing-logging/badge.svg)](https://pypi.python.org/pypi/multiprocessing-logging/)
[![Development Status](https://pypip.in/status/multiprocessing-logging/badge.svg)](https://pypi.python.org/pypi/multiprocessing-logging/)
[![Download format](https://pypip.in/format/multiprocessing-logging/badge.svg)](https://pypi.python.org/pypi/multiprocessing-logging/)
[![License](https://pypip.in/license/multiprocessing-logging/badge.svg)](https://pypi.python.org/pypi/multiprocessing-logging/)


When using the `multiprocessing` module, logging becomes less useful since
sub-processes should log to individual files/streams or there's the risk of
records becoming garbled.

This simple module implements a `Handler` that when set on the root
`Logger` will handle tunneling the records to the main process so that
they are handled correctly.

Unfortunately, this technique only works with Processes and not with a Pool
of processes. If you need this, I'd welcome a pull request! :)

It's currently tested in Linux and Python 2.7 and 3.3+.


# Origin

This library was taken verbatim from a [StackOverflow post](http://stackoverflow.com/questions/641420/how-should-i-log-while-using-multiprocessing-in-python)
and extracted into a module so that I wouldn't have to copy the code in every
project.

Later, several improvements have been contributed.

# Usage

Before you start logging but after you configure the logging framework (maybe with `logging.basicConfig(...)`), do the following:

    import multiprocessing_logging

    multiprocessing_logging.install_mp_handler()

and that's it.

## With multiprocessing.Pool

When using a Pool, the process workers instantiated by the Pool will not initialize multiprocessing-logging handlers automatically.
It has to be done in the initilizer like this:

    from multiprocessing import Pool
    import multiprocessing_logging

    pool = Pool(42, initializer=multiprocessing_logging.install_mp_handler)
