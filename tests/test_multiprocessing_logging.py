#!/usr/bin/env python
# vim : fileencoding=UTF-8 :

from __future__ import absolute_import, division, unicode_literals

import logging
import multiprocessing as mp
import os
import random
import re
import tempfile
import time
import unittest
from io import StringIO

try:
    import queue
    from unittest import mock
except ImportError:  # Python 2.
    import mock  # type: ignore[no-redef]
    import Queue as queue  # type: ignore[no-redef]

    BrokenPipeError = OSError

from multiprocessing_logging import install_mp_handler, MultiProcessingHandler, uninstall_mp_handler


class UninstallHandlersTest(unittest.TestCase):
    def test_when_uninstall_is_repeated_then_it_stops_receivers_and_keeps_the_file_handler(self):
        with tempfile.NamedTemporaryFile() as output:
            original = logging.FileHandler(output.name, mode="w")
            logger = logging.Logger("uninstall-file-handler")
            logger.addHandler(original)
            wrappers = []
            try:
                for iteration in range(3):
                    install_mp_handler(logger)
                    wrapper = logger.handlers[0]
                    wrappers.append(wrapper)
                    logger.warning("queued %d", iteration)
                    uninstall_mp_handler(logger)

                    self.assertEqual([original], logger.handlers)
                    self.assertFalse(wrapper._receive_thread.is_alive())
                    self.assertTrue(wrapper.queue._reader.closed)
                    self.assertTrue(wrapper.queue._writer.closed)
                    wrapper.close()
                    self.assertFalse(original.stream.closed)
                    os.fstat(original.stream.fileno())
                    logger.warning("direct %d", iteration)

                uninstall_mp_handler(logger)
                original.flush()
                with open(output.name) as result:
                    self.assertEqual(
                        "".join("queued %d\ndirect %d\n" % (i, i) for i in range(3)),
                        result.read(),
                    )
            finally:
                for wrapper in wrappers:
                    wrapper.close()
                original.close()

    def test_when_a_child_has_completed_then_uninstall_drains_its_records(self):
        stream = StringIO()
        original = logging.StreamHandler(stream)
        logger = logging.Logger("uninstall-child")
        logger.addHandler(original)
        install_mp_handler(logger)
        wrapper = logger.handlers[0]

        def worker():
            for number in range(20):
                logger.warning("child %d", number)

        process = mp.Process(target=worker)
        try:
            process.start()
            process.join(5)
            self.assertFalse(process.is_alive())
            self.assertEqual(0, process.exitcode)
            uninstall_mp_handler(logger)
            logger.warning("parent resumed")
            self.assertFalse(wrapper._receive_thread.is_alive())
            self.assertEqual(
                "".join("child %d\n" % i for i in range(20)) + "parent resumed\n",
                stream.getvalue(),
            )
        finally:
            if process.is_alive():
                process.terminate()
                process.join()
            wrapper.close()
            original.close()


class InstallHandlersTest(unittest.TestCase):
    def setUp(self):
        self.handler = logging.NullHandler()
        self.logger = logging.Logger("test-logger")
        self.logger.addHandler(self.handler)

    def _assert_result(self):
        (wrapper_handler,) = self.logger.handlers
        self.assertIsInstance(wrapper_handler, MultiProcessingHandler)
        self.assertIs(wrapper_handler.sub_handler, self.handler)

    def test_when_no_logger_is_specified_then_it_uses_the_root_logger(self):
        with mock.patch("logging.getLogger") as getLogger:
            getLogger.return_value = self.logger

            install_mp_handler()

            getLogger.assert_called_once_with()

        (wrapper_handler,) = self.logger.handlers
        self.assertIsInstance(wrapper_handler, MultiProcessingHandler)
        self.assertIs(wrapper_handler.sub_handler, self.handler)

    def test_when_a_logger_is_passed_then_it_does_not_change_the_root_logger(self):
        root = logging.getLogger()
        root_handlers = list(root.handlers)

        with mock.patch("logging.getLogger") as getLogger:
            install_mp_handler(self.logger)

        self.assertEqual(0, getLogger.call_count)
        self.assertEqual(root_handlers, root.handlers)

    def test_when_a_logger_is_passed_then_it_wraps_all_handlers(self):
        second_handler = logging.NullHandler()
        self.logger.addHandler(second_handler)

        install_mp_handler(self.logger)

        first_wrapper, second_wrapper = self.logger.handlers
        self.assertIsInstance(first_wrapper, MultiProcessingHandler)
        self.assertIs(first_wrapper.sub_handler, self.handler)
        self.assertIsInstance(second_wrapper, MultiProcessingHandler)
        self.assertIs(second_wrapper.sub_handler, second_handler)


class WhenMultipleProcessesLogRecords(unittest.TestCase):
    handlers = ()

    def setUp(self):
        self.stream = StringIO()
        self.subject = MultiProcessingHandler(
            "mp-handler",
            logging.StreamHandler(stream=self.stream),
        )

        logger = logging.getLogger()

        self.handlers = logger.handlers
        for handler in self.handlers:
            logger.removeHandler(handler)

        logger.addHandler(self.subject)

    def tearDown(self):
        self.subject.close()
        logger = logging.getLogger()
        logger.removeHandler(self.subject)

        for handler in self.handlers:
            logger.addHandler(handler)

    def test_when_multiple_processes_log_then_records_are_not_garbled(self):
        def worker(wid):
            logger = logging.getLogger()

            logger.critical("Worker %d started.", wid)

            time.sleep(random.random())

            logger.critical("Worker %d finished processing.", wid)

        logger = logging.getLogger()

        procs = [mp.Process(target=worker, args=(wid,)) for wid in range(100)]
        logger.critical("Starting workers...")
        for proc in procs:
            proc.start()
        logger.critical("Workers started.")

        hanged = 0
        for proc in procs:
            proc.join(1.5)
            if proc.is_alive():
                hanged += 1
                proc.terminate()
        logger.critical("Workers done.")

        self.subject.close()
        self.stream.seek(0)
        lines = self.stream.readlines()
        self.assertIn("Starting workers...\n", lines)
        self.assertIn("Workers started.\n", lines)
        self.assertEqual("Workers done.\n", lines[-1])

        valid_line = re.compile(
            r"(?:"
            r"(?:Starting workers...)"
            r"|(?:Worker \d+ started\.)"
            r"|(?:Workers started\.)"
            r"|(?:Worker \d+ finished processing\.)"
            r"|(?:Workers done.)"
            r")$"
        )
        for line in lines:
            self.assertTrue(re.match(valid_line, line))

        self.assertEqual(0, hanged, "Childs hanged")

    def test_when_the_handler_is_closed_then_it_keeps_the_last_record_sent(self):
        logger = logging.getLogger()

        logger.critical("Last record.")

        self.subject.close()

        value = self.stream.getvalue()
        self.assertEqual("Last record.\n", value)

    def test_when_children_log_then_it_passes_all_logs(self):
        def worker(wid):
            logger = logging.getLogger()
            for _ in range(10):
                logger.critical("Worker %d log.", wid)

        logger = logging.getLogger()

        logger.critical("Starting workers...")
        procs = [mp.Process(target=worker, args=(wid,)) for wid in range(2)]
        for proc in procs:
            proc.start()
        logger.critical("Workers started.")

        for proc in procs:
            proc.join()
        logger.critical("Workers done.")

        self.subject.close()
        self.stream.seek(0)
        lines = self.stream.readlines()
        self.assertIn("Starting workers...\n", lines)
        self.assertIn("Workers started.\n", lines)
        self.assertIn("Workers done.\n", lines)
        self.assertEqual(10, lines.count("Worker 0 log.\n"))
        self.assertEqual(10, lines.count("Worker 1 log.\n"))
        self.assertEqual(10 * 2 + 3, len(lines))

    def test_when_the_connection_to_the_child_process_breaks_then_it_closes_the_queue(self):
        with mock.patch(
            "multiprocessing_logging.multiprocessing.Queue",
            autospec=True,
        ) as queue_class:
            # autospec failed.
            queue_inst = queue_class.return_value
            queue_inst.get.side_effect = queue.Empty()
            queue_inst.qsize.side_effect = BrokenPipeError("error on qsize")

            subject = MultiProcessingHandler(
                "mp-handler",
                logging.StreamHandler(stream=self.stream),
            )
            logging.getLogger().addHandler(subject)
            try:
                time.sleep(0.1)
                subject.close()
            finally:
                logging.getLogger().removeHandler(subject)

            queue_inst.get.assert_called()
            queue_inst.close.assert_called_once_with()

    def test_when_a_child_exits_then_it_does_not_close_the_queue_for_the_parent(self):
        def worker(wid):
            logger = logging.getLogger("child.%d" % (wid,))
            for i in range(3):
                logger.critical("Log %d.", i)

        logger = logging.getLogger()

        logger.critical("Starting first batch of workers...")
        procs = [mp.Process(target=worker, args=(wid,)) for wid in range(2)]
        for proc in procs:
            proc.start()
        logger.critical("First batch workers started.")
        for proc in procs:
            proc.join()
        logger.critical("First batch workers done.")

        logger.critical("Starting second batch of workers...")
        procs = [mp.Process(target=worker, args=(wid,)) for wid in range(2, 3)]
        for proc in procs:
            proc.start()
        logger.critical("Second batch of workers started.")
        for proc in procs:
            proc.join()
        logger.critical("Second batch of workers done.")

        self.subject.close()
        self.stream.seek(0)
        lines = self.stream.readlines()
        self.assertEqual(3 * (2 + 1) + 2 * 3, len(lines), lines)


if __name__ == "__main__":
    unittest.main()
