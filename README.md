# multiprocessing-logging

[![Run Status](https://api.shippable.com/projects/57c8a389407d610f0052c211/badge?branch=master)](https://app.shippable.com/projects/57c8a389407d610f0052c211)
[![Coverage Badge](https://api.shippable.com/projects/57c8a389407d610f0052c211/coverageBadge?branch=master)](https://app.shippable.com/projects/57c8a389407d610f0052c211)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/multiprocessing-logging.svg)](https://pypi.python.org/pypi/multiprocessing-logging/)
[![License](https://img.shields.io/pypi/l/multiprocessing-logging.svg)](https://pypi.python.org/pypi/multiprocessing-logging/)


When using the `multiprocessing` module, logging becomes less useful since
sub-processes should log to individual files/streams or there's the risk of
records becoming garbled.

This simple module implements a `Handler` that when set on the root
`Logger` will handle tunneling the records to the main process so that
they are handled correctly.

It's currently tested in Linux and Python 2.7, 3.3+, pypy & pypy3.

It does not work on Windows and I believe it could not work.

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

When using a Pool, the process workers instantiated by the Pool will not initialize multiprocessing-logging handlers automatically. Currently, there's no solution for this.
