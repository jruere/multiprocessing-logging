#!/usr/bin/env python
# vim : fileencoding=UTF-8 :

from __future__ import absolute_import, division, unicode_literals

from io import StringIO
import logging
import multiprocessing as mp
import random
import re
import time
import unittest

from multiprocessing_logging import MultiProcessingHandler


class WhenMultipleProcessesLog(unittest.TestCase):

    def test_then_records_should_not_be_garbled(self):
        stream = StringIO()
        subject = MultiProcessingHandler(
            'mp-handler', logging.StreamHandler(stream=stream))
        logger = logging.Logger('root')
        logger.addHandler(subject)

        def worker(wid, logger):
            logger.info("Worker %d started.", wid)

            time.sleep(random.random())

            logger.info("Worker %d finished processing.", wid)

        logger.info("Starting workers...")
        procs = [mp.Process(target=worker, args=(wid, logger)) for wid in range(100)]
        for proc in procs:
            proc.daemon = True
            proc.start()

        logger.info("Workers started.")
        time.sleep(1)

        for proc in procs:
            proc.join(timeout=1)
        logger.info("Workers done.")

        time.sleep(0.5)  # For log records to propagate.

        subject.sub_handler.flush()
        subject.close()
        stream.seek(0)
        lines = stream.readlines()
        self.assertIn("Starting workers...\n", lines)
        self.assertIn("Workers done.\n", lines)

        valid_line = re.compile(
            r"(?:Starting workers...)"
            r"|(?:Worker \d+ started\.)"
            r"|(?:Workers started\.)"
            r"|(?:Worker \d+ finished processing\.)"
            r"|(?:Workers done.)"
        )
        for line in lines[1:-1]:
            self.assertTrue(re.match(valid_line, line))


if __name__ == '__main__':
    unittest.main()
