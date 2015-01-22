# multiprocessing-logging

When using the `multiprocessing` library, logging become less useful since
since sub-processes should log to individual files/streams or there's the
risk of records becoming garbled.

This simple library implements a `Handler` that when set on the root
`Logger` will handle tunneling the records to the main process so that
they are handled correctly.

It's currently tested in Linux and Python 2.7.


# Origin

This library was taken verbatim from a [StackOverflow post](http://stackoverflow.com/questions/641420/how-should-i-log-while-using-multiprocessing-in-python)
and extracted into a library so that I wouldn't have to copy the code in every project.

# Usage

When configuring logging, do the following:

    logging.getLogger().addHandler(
        multiprocessing_logging.MultiProcessingHandler('worker-logger'))

and that's it.
