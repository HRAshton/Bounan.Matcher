import concurrent.futures
import logging
from concurrent.futures import Future
from typing import Callable, TypeVar, Dict

from dotenv import load_dotenv

from Matcher.config.config import Config
from Matcher.matcher_logger import setup_logging

A = TypeVar('A')
R = TypeVar('R')

USE_MULTIPROCESSING = True  # Use False to prevent PyCharm debug issues

pool = concurrent.futures.ProcessPoolExecutor(max_workers=1)
results: Dict[int, Callable[[], R]] = {}

logger = logging.getLogger(__name__)


def init_pre_request_queue() -> None:
    global results
    results.clear()
    logger.info('Queue was reset.')


def pre_request(key: int, func: Callable[[A], R], *args: A) -> None:
    global results
    assert key not in results
    assert len(results) < 2
    if USE_MULTIPROCESSING:
        future = _run_in_subprocess(func, *args)
        results[key] = lambda: future.result()
    else:
        logger.warning("Multiprocessing is disabled")
        results[key] = lambda: func(*args)


def get_result(key: int) -> R:
    global results
    wav_path, current_duration = results[key]()
    del results[key]

    return wav_path, current_duration


def _run_in_subprocess(func: Callable[[A], R], *args: A) -> Future[R]:
    return pool.submit(_run_with_logger, func, *args)


def _run_with_logger(func: Callable[[A], R], *args: A) -> R:
    # This function is executed in a subprocess, so we need to set up environment again
    load_dotenv()
    Config.initialize_from_env()
    setup_logging()
    return func(*args)
