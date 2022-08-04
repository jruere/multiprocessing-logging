# vim : fileencoding=UTF-8 :

import atexit
import logging
import multiprocessing
import signal
import sys
import threading

from queue import Empty

__version__ = "0.3.4"


_sig_handler_lock = multiprocessing.Lock()
_sig_handler_registered = False
_prev_sig_handler = None

def _sig_handler(signum, frame):
    if _prev_sig_handler not in [signal.SIG_IGN, signal.SIG_DFL, None]:
        signal.signal(signum, _prev_sig_handler)

    # Forces atexit events to run when SIGTERM occurs
    sys.exit(0)

def  _run_on_exit(func):
    global _sig_handler_registered
    global _prev_sig_handler

    with _sig_handler_lock:
        if not _sig_handler_registered:
            _prev_sig_handler = signal.signal(signal.SIGTERM, _sig_handler)
            _sig_handler_registered = True

        atexit.register(func)
        
def install_mp_handler(logger=None):
    """Wraps the handlers in the given Logger with an MultiProcessingHandler.

    :param logger: whose handlers to wrap. By default, the root logger.
    """
    if logger is None:
        logger = logging.getLogger()

    for i, orig_handler in enumerate(list(logger.handlers)):
        handler = MultiProcessingHandler("mp-handler-{0}".format(i), sub_handler=orig_handler)

        logger.removeHandler(orig_handler)
        logger.addHandler(handler)


def uninstall_mp_handler(logger=None):
    """Unwraps the handlers in the given Logger from a MultiProcessingHandler wrapper

    :param logger: whose handlers to unwrap. By default, the root logger.
    """
    if logger is None:
        logger = logging.getLogger()

    for handler in logger.handlers:
        if isinstance(handler, MultiProcessingHandler):
            orig_handler = handler.sub_handler
            logger.removeHandler(handler)
            logger.addHandler(orig_handler)


class MultiProcessingHandler(logging.Handler):
    def __init__(self, name, sub_handler=None):
        super(MultiProcessingHandler, self).__init__()

        if sub_handler is None:
            sub_handler = logging.StreamHandler()
        self.sub_handler = sub_handler

        self.setLevel(self.sub_handler.level)
        self.setFormatter(self.sub_handler.formatter)
        self.filters = self.sub_handler.filters

        self.queue = multiprocessing.Queue(-1)
        self._is_closed = False
        # The thread handles receiving records asynchronously.
        self._receive_thread = threading.Thread(target=self._receive, name=name)
        self._receive_thread.daemon = True
        self._receive_thread.start()

        _run_on_exit(self.close)

    def setFormatter(self, fmt):
        super(MultiProcessingHandler, self).setFormatter(fmt)
        self.sub_handler.setFormatter(fmt)

    def _receive(self):
        while True:
            try:
                if self._is_closed and self.queue.empty():
                    break

                record = self.queue.get(timeout=0.2)
                self.sub_handler.emit(record)
            except (KeyboardInterrupt, SystemExit):
                raise
            except (OSError, EOFError):
                break  # The queue was closed by child?
            except Empty:
                pass  # This periodically checks if the logger is closed.
            except:
                from sys import stderr
                from traceback import print_exc

                print_exc(file=stderr)
                raise

        self.queue.close()
        self.queue.join_thread()

    def _send(self, s):
        self.queue.put_nowait(s)

    def _format_record(self, record):
        # ensure that exc_info and args
        # have been stringified. Removes any chance of
        # unpickleable things inside and possibly reduces
        # message size sent over the pipe.
        if record.args:
            record.msg = record.msg % record.args
            record.args = None
        if record.exc_info:
            self.format(record)
            record.exc_info = None

        return record

    def emit(self, record):
        try:
            s = self._format_record(record)
            self._send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        if not self._is_closed:
            self._is_closed = True
            self._receive_thread.join(5.0)  # Waits for receive queue to empty.

            self.sub_handler.close()
            super(MultiProcessingHandler, self).close()
