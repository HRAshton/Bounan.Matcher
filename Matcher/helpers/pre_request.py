import concurrent.futures
import logging
from typing import Callable, TypeVar, Generic, ParamSpec

from dotenv import load_dotenv

from Matcher.config.config import Config
from Matcher.matcher_logger import setup_logging

TArgs = ParamSpec('TArgs')
TResult = TypeVar('TResult')

USE_MULTIPROCESSING = True  # Use False to prevent PyCharm debug issues

logger = logging.getLogger(__name__)


class PreRequestQueue(Generic[TArgs, TResult]):
    _pool: concurrent.futures.ProcessPoolExecutor | None
    _results: dict[int, Callable[[], TResult]]

    def __init__(self, config: dict[str, str]):
        if USE_MULTIPROCESSING:
            self._pool = concurrent.futures.ProcessPoolExecutor(
                max_workers=1,
                initializer=PreRequestQueue._init_worker,
                initargs=(config,))

        self._results: dict[int, Callable[[], TResult]] = {}

    def __enter__(self):
        logger.info("Queue initialized.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._pool:
            self._pool.shutdown(wait=True)
        self._results.clear()
        logger.info("Queue was reset and resources released.")

    def pre_request(self, key: int,
                    func: Callable[TArgs, TResult],
                    *args: TArgs.args,
                    **kwargs: TArgs.kwargs) -> None:
        assert key not in self._results
        assert len(self._results) < 2
        assert kwargs == {}, "Keyword arguments are not needed for now"

        if self._pool:
            future = self._pool.submit(self._run_with_logger,
                                       func,
                                       *args,
                                       **kwargs)
            self._results[key] = lambda: future.result()
        else:
            logger.warning("Multiprocessing is disabled")
            self._results[key] = lambda: func(*args, **kwargs)

    def pop_result(self, key: int) -> TResult:
        res = self._results[key]()
        del self._results[key]
        return res

    @staticmethod
    def _init_worker(config: dict[str, str]) -> None:
        load_dotenv()
        Config.initialize_from_dict(config)
        setup_logging()

    @staticmethod
    def _run_with_logger(func: Callable[TArgs, TResult],
                         *args: TArgs.args,
                         **kwargs: TArgs.kwargs) -> TResult:
        return func(*args, **kwargs)
