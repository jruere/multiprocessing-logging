# vim : fileencoding=UTF-8 :

from __future__ import absolute_import, division, unicode_literals

import logging
import multiprocessing
import sys
import threading
import traceback


__version__ = '0.2.4'


def install_mp_handler(logger=None):
    """Wraps the handlers in the given Logger with an MultiProcessingHandler.

    :param logger: whose handlers to wrap. By default, the root logger.
    """
    if logger is None:
        logger = logging.getLogger()

    for i, orig_handler in enumerate(list(logger.handlers)):
        handler = MultiProcessingHandler(
            'mp-handler-{0}'.format(i), sub_handler=orig_handler)

        logger.removeHandler(orig_handler)
        logger.addHandler(handler)


class MultiProcessingHandler(logging.Handler):

    def __init__(self, name, sub_handler=None):
        super(MultiProcessingHandler, self).__init__()

        if sub_handler is None:
            sub_handler = logging.StreamHandler()

        self.sub_handler = sub_handler
        self.queue = multiprocessing.Queue(-1)
        self.setLevel(self.sub_handler.level)
        self.setFormatter(self.sub_handler.formatter)
        # The thread handles receiving records asynchronously.
        t = threading.Thread(target=self.receive, name=name)
        t.daemon = True
        t.start()

    def setFormatter(self, fmt):
        logging.Handler.setFormatter(self, fmt)
        self.sub_handler.setFormatter(fmt)

    def receive(self):
        while True:
            try:
                record = self.queue.get()
                self.sub_handler.emit(record)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except:
                traceback.print_exc(file=sys.stderr)

    def send(self, s):
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
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        self.sub_handler.close()
        logging.Handler.close(self)
        self.queue.close()
        self.queue.join_thread()
