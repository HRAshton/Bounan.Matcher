import os


class _Config:
    @property
    def log_group_name(self) -> str:
        return os.environ.get('LOG_GROUP_NAME')

    @property
    def log_level(self) -> str:
        return os.environ.get('LOG_LEVEL', 'INFO')

    @property
    def episodes_to_match(self) -> int:
        return os.environ.get('EPISODES_TO_MATCH', 5)

    @property
    def seconds_to_match(self) -> int:
        return int(os.environ.get('SECONDS_TO_MATCH', 6 * 60))

    @property
    def notification_queue_url(self) -> str:
        return os.environ.get('VIDEO_REGISTERED_QUEUE_URL')

    @property
    def get_series_to_match_lambda_name(self) -> str:
        return os.environ.get('GET_SERIES_TO_MATCH_LAMBDA_NAME')

    @property
    def update_video_scenes_lambda_name(self) -> str:
        return os.environ.get('UPDATE_VIDEO_SCENES_LAMBDA_NAME')

    @property
    def temp_dir(self) -> str:
        return os.environ.get('TEMP_DIR', '/tmp')

    @property
    def download_threads(self) -> int:
        return int(os.environ.get('DOWNLOAD_THREADS', 12))

    @property
    def download_max_retries_for_ts(self) -> int:
        return int(os.environ.get('DOWNLOAD_MAX_RETRIES_FOR_TS', 3))

    @property
    def scene_after_opening_threshold_secs(self) -> int:
        return int(os.environ.get('SCENE_AFTER_OPENING_THRESHOLD', 4))

    @property
    def min_scene_length_secs(self) -> int:
        return int(os.environ.get('MIN_SCENE_LENGTH_SECS', 20))

    @property
    def operating_log_rate_per_minute(self) -> int:
        return int(os.environ.get('OPERATING_LOG_RATE_PER_MINUTE', 1))

    @property
    def batch_size(self) -> int:
        return int(os.environ.get('BATCH_SIZE', 30))


Config = _Config()
