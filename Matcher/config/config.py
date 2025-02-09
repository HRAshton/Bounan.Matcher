import os
from typing import TypeVar

T = TypeVar("T")


class _Config:
    @property
    def log_group_name(self) -> str:
        return _Config.get_value('LOG_GROUP_NAME')

    @property
    def log_level(self) -> str:
        return _Config.get_value('LOG_LEVEL', 'INFO')

    @property
    def episodes_to_match(self) -> int:
        return int(_Config.get_value('EPISODES_TO_MATCH', 5))

    @property
    def seconds_to_match(self) -> int:
        return int(_Config.get_value('SECONDS_TO_MATCH', 6 * 60))

    @property
    def notification_queue_url(self) -> str:
        return _Config.get_value('VIDEO_REGISTERED_QUEUE_URL')

    @property
    def get_series_to_match_lambda_name(self) -> str:
        return _Config.get_value('GET_SERIES_TO_MATCH_LAMBDA_NAME')

    @property
    def update_video_scenes_lambda_name(self) -> str:
        return _Config.get_value('UPDATE_VIDEO_SCENES_LAMBDA_NAME')

    @property
    def temp_dir(self) -> str:
        return _Config.get_value('TEMP_DIR', '/tmp')

    @property
    def download_threads(self) -> int:
        return int(_Config.get_value('DOWNLOAD_THREADS', 12))

    @property
    def download_max_retries_for_ts(self) -> int:
        return int(_Config.get_value('DOWNLOAD_MAX_RETRIES_FOR_TS', 3))

    @property
    def scene_after_opening_threshold_secs(self) -> int:
        return int(_Config.get_value('SCENE_AFTER_OPENING_THRESHOLD', 4))

    @property
    def min_scene_length_secs(self) -> int:
        return int(_Config.get_value('MIN_SCENE_LENGTH_SECS', 20))

    @property
    def operating_log_rate_per_minute(self) -> int:
        return int(_Config.get_value('OPERATING_LOG_RATE_PER_MINUTE', 1))

    @property
    def batch_size(self) -> int:
        # 20 is set to avoid rate limits on Publisher side.
        # It will automatically expand up to 10*2-1=19
        # if last batch contains less than 10 videos.
        return int(_Config.get_value('BATCH_SIZE', 10))

    @staticmethod
    def get_value(key: str, default: T | None = None) -> str | T:
        value = os.environ.get(key, default)
        assert value is not None, f"Environment variable {key} is not set"
        return value


Config = _Config()
