import concurrent.futures
from concurrent.futures import Future
from typing import Callable, TypeVar, Dict

from matcher_logger import setup_logging

A = TypeVar('A')
R = TypeVar('R')

USE_MULTIPROCESSING = False  # Set False to prevent PyCharm debug issues

pool = concurrent.futures.ProcessPoolExecutor(max_workers=1)
results: Dict[int, Callable[[], R]] = {}


def _run_with_logger(func: Callable[[A], R], *args: A) -> R:
    # This function is executed in a subprocess, so we need to set up logging
    setup_logging()
    return func(*args)


def _run_in_subprocess(func: Callable[[A], R], *args: A) -> Future[R]:
    return pool.submit(_run_with_logger, func, *args)


def pre_request(key: int, func: Callable[[A], R], *args: A) -> None:
    global results
    assert key not in results
    assert len(results) < 2
    if USE_MULTIPROCESSING:
        future = _run_in_subprocess(func, *args)
        results[key] = lambda: future.result()
    else:
        results[key] = lambda: func(*args)


def get_result(key: int) -> R:
    global results
    wav_path, current_duration = results[key]()
    del results[key]

    return wav_path, current_duration
