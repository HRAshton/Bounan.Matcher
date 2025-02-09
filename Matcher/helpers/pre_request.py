import concurrent.futures
import logging
from concurrent.futures import Future
from typing import Callable, TypeVar, Dict, Generic

from dotenv import load_dotenv

from Matcher.config.config import Config
from Matcher.matcher_logger import setup_logging

A = TypeVar('A')
R = TypeVar('R')

USE_MULTIPROCESSING = True  # Use False to prevent PyCharm debug issues

logger = logging.getLogger(__name__)


class PreRequestQueue(Generic[A, R]):
    def __init__(self):
        self.pool = concurrent.futures.ProcessPoolExecutor(max_workers=1) \
            if USE_MULTIPROCESSING \
            else None
        self.results: Dict[int, Callable[[], R]] = {}

    def __enter__(self):
        logger.info("Queue initialized.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pool:
            self.pool.shutdown(wait=True)
        self.results.clear()
        logger.info("Queue was reset and resources released.")

    def pre_request(self, key: int, func: Callable[[A], R], *args: A) -> None:
        assert key not in self.results
        assert len(self.results) < 2

        if self.pool:
            future = self._run_in_subprocess(func, *args)
            self.results[key] = lambda: future.result()
        else:
            logger.warning("Multiprocessing is disabled")
            self.results[key] = lambda: func(*args)

    def get_result(self, key: int) -> R:
        res = self.results[key]()
        del self.results[key]
        return res

    def _run_in_subprocess(self, func: Callable[[A], R], *args: A) -> Future[R]:
        return self.pool.submit(self._run_with_logger, func, *args)

    @staticmethod
    def _run_with_logger(func: Callable[[A], R], *args: A) -> R:
        # This function is executed in a subprocess, so we need to set up environment again
        load_dotenv()
        Config.initialize_from_env()
        setup_logging()
        return func(*args)
