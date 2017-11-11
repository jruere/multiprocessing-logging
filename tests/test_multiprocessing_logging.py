#!/usr/bin/env python
# vim : fileencoding=UTF-8 :

from __future__ import absolute_import, division, unicode_literals

import logging
import multiprocessing as mp
import random
import re
import time
import unittest
from io import StringIO

try:
    from unittest import mock
except ImportError:
    mock = None

from multiprocessing_logging import install_mp_handler, MultiProcessingHandler


class InstallHandlersTest(unittest.TestCase):

    def setUp(self):
        self.handler = logging.NullHandler()
        self.logger = logging.Logger('test-logger')
        self.logger.addHandler(self.handler)

    def _assert_result(self):
        wrapper_handler, = self.logger.handlers
        self.assertIsInstance(wrapper_handler, MultiProcessingHandler)
        self.assertIs(wrapper_handler.sub_handler, self.handler)

    def test_when_no_logger_is_specified_then_it_uses_the_root_logger(self):
        if not mock:
            self.skipTest('unittest.mock is not available')

        with mock.patch('logging.getLogger') as getLogger:
            getLogger.return_value = self.logger

            install_mp_handler()

            getLogger.assert_called_once_with()

        wrapper_handler, = self.logger.handlers
        self.assertIsInstance(wrapper_handler, MultiProcessingHandler)
        self.assertIs(wrapper_handler.sub_handler, self.handler)

    def test_when_a_logger_is_passed_then_it_does_not_change_the_root_logger(self):
        if not mock:
            self.skipTest('unittest.mock is not available')

        with mock.patch('logging.getLogger') as getLogger:
            install_mp_handler(self.logger)

            self.assertEqual(0, getLogger.call_count)

    def test_when_a_logger_is_passed_then_it_wraps_all_handlers(self):
        install_mp_handler(self.logger)

        wrapper_handler, = self.logger.handlers
        self.assertIsInstance(wrapper_handler, MultiProcessingHandler)
        self.assertIs(wrapper_handler.sub_handler, self.handler)


class WhenMultipleProcessesLogRecords(unittest.TestCase):

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

        for proc in procs:
            proc.join()
        logger.info("Workers done.")

        subject.close()
        stream.seek(0)
        lines = stream.readlines()
        self.assertIn("Starting workers...\n", lines)
        self.assertIn("Workers started.\n", lines)
        self.assertEqual("Workers done.\n", lines[-1])

        valid_line = re.compile(
            r"(?:Starting workers...)"
            r"|(?:Worker \d+ started\.)"
            r"|(?:Workers started\.)"
            r"|(?:Worker \d+ finished processing\.)"
            r"|(?:Workers done.)"
        )
        for line in lines:
            self.assertTrue(re.match(valid_line, line))

    def test_then_it_should_keep_the_last_record_sent(self):
        stream = StringIO()
        subject = MultiProcessingHandler(
            'mp-handler', logging.StreamHandler(stream=stream))
        logger = logging.Logger('root')
        logger.addHandler(subject)

        logger.info("Last record.")

        subject.close()

        value = stream.getvalue()
        self.assertEqual('Last record.\n', value)

    def test_then_it_should_pass_all_logs(self):
        stream = StringIO()
        subject = MultiProcessingHandler(
            'mp-handler', logging.StreamHandler(stream=stream))
        logger = logging.Logger('root')
        logger.addHandler(subject)

        def worker(wid, logger):
            for _ in range(10):
                logger.info("Worker %d log.", wid)

        logger.info("Starting workers...")
        procs = [mp.Process(target=worker, args=(wid, logger)) for wid in range(2)]
        for proc in procs:
            proc.daemon = True
            proc.start()
        logger.info("Workers started.")

        for proc in procs:
            proc.join()
        logger.info("Workers done.")

        subject.close()

        stream.seek(0)
        lines = stream.readlines()
        self.assertIn("Starting workers...\n", lines)
        self.assertIn("Workers started.\n", lines)
        self.assertIn("Workers done.\n", lines)
        self.assertEqual(10 * 2 + 3, len(lines))


if __name__ == '__main__':
    unittest.main()
