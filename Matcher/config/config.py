import json
import os
from typing import TypeVar

from Matcher.clients import ssm_client

T = TypeVar("T")

PARAMETER_NAME = os.environ.get('CONFIGURATION_PARAMETER_NAME')


class _Config:
    _configuration: dict[str, str] | None = None

    def initialize_from_ssm(self) -> None:
        runtime_config_json = ssm_client.get_ssm_parameter(PARAMETER_NAME)
        self._configuration = json.loads(runtime_config_json)

    def initialize_from_dict(self, configuration: dict[str, str]) -> None:
        self._configuration = configuration

    def export(self) -> dict[str, str]:
        return dict(self._configuration)

    @property
    def loan_api_token(self) -> str:
        return self._get_value('loan_api_token')

    @property
    def log_group_name(self) -> str:
        return self._get_value('log_group_name')

    @property
    def log_level(self) -> str:
        return self._get_value('log_level', 'INFO')

    @property
    def episodes_to_match(self) -> int:
        return int(self._get_value('episodes_to_match', 5))

    @property
    def seconds_to_match(self) -> int:
        return int(self._get_value('seconds_to_match', 6 * 60))

    @property
    def notification_queue_url(self) -> str:
        return self._get_value('notification_queue_url')

    @property
    def get_series_to_match_lambda_name(self) -> str:
        return self._get_value('get_series_to_match_lambda_name')

    @property
    def update_video_scenes_lambda_name(self) -> str:
        return self._get_value('update_video_scenes_lambda_name')

    @property
    def temp_dir(self) -> str:
        return self._get_value('temp_dir', '/tmp')

    @property
    def download_threads(self) -> int:
        return int(self._get_value('download_threads', 12))

    @property
    def download_max_retries_for_ts(self) -> int:
        return int(self._get_value('download_max_retries_for_ts', 3))

    @property
    def scene_after_opening_threshold_secs(self) -> int:
        return int(self._get_value('scene_after_opening_threshold_secs', 4))

    @property
    def min_scene_length_secs(self) -> int:
        return int(self._get_value('min_scene_length_secs', 20))

    @property
    def operating_log_rate_per_minute(self) -> int:
        return int(self._get_value('operating_log_rate_per_minute', 1))

    @property
    def batch_size(self) -> int:
        # 20 is set to avoid rate limits on Publisher side.
        # It will automatically expand up to 10*2-1=19
        # if last batch contains less than 10 videos.
        return int(self._get_value('batch_size', 10))

    def _get_value(self, key: str, default: T | None = None) -> str | T:
        value = os.environ.get(key) or self._configuration.get(key, default)
        assert value is not None, f"Configuration value for '{key}' is not set."
        return value


Config = _Config()
