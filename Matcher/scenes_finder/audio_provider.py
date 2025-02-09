import logging
import os
from typing import Iterator

import m3u8

from Matcher.config.config import Config
from Matcher.helpers.not_none import not_none
from Matcher.helpers.pre_request import PreRequestQueue
from Matcher.scenes_finder.audio_merger import download_and_merge_parts

logger = logging.getLogger(__name__)


class AudioProvider:
    """Class that downloads and merges audio segments into a single wav file."""

    DELETE_TEMP_FILES = True  # Set to False for debugging purposes

    file_path_to_delete: str | None = None
    truncated_durations_per_episode: list[float] = []

    initialized: bool = False
    completed: bool = False

    playlists: list[m3u8.M3U8]
    opening: bool

    def __init__(self, playlists: list[m3u8.M3U8], opening: bool):
        self.playlists = playlists
        self.opening = opening

    def get_iterator(self) -> Iterator[tuple[str, float, float]]:
        """Generator that downloads and merges .wav files for each playlist."""
        assert not self.initialized, "WavProcessor cannot be used twice."
        self.initialized = True

        if len(self.playlists) < 2:
            self.completed = True
            return

        config_dict = Config.export()
        with PreRequestQueue[[m3u8.M3U8, bool, int], tuple[str, float]](config_dict) as queue:
            queue.pre_request(0, self._get_wav, self.playlists[0], self.opening, 0)

            for i, playlist in enumerate(self.playlists):
                if self.file_path_to_delete and self.DELETE_TEMP_FILES and os.path.exists(self.file_path_to_delete):
                    os.remove(self.file_path_to_delete)

                # Retrieve previous request result
                wav_path, segments_duration = queue.pop_result(i)
                if i + 1 < len(self.playlists):
                    # Start next download in advance
                    queue.pre_request(i + 1, self._get_wav, self.playlists[i + 1], self.opening, i + 1)

                truncated_duration = min(segments_duration, Config.seconds_to_match)
                offset = 0 if self.opening else max(segments_duration - Config.seconds_to_match, 0)

                self.truncated_durations_per_episode.append(truncated_duration)
                self.file_path_to_delete = wav_path

                yield wav_path, offset, truncated_duration

        self.completed = True

    @property
    def truncated_durations(self) -> list[float]:
        """Returns the list of truncated durations per episode."""
        assert self.completed, "WavProcessor must be completed before calling this method."
        return self.truncated_durations_per_episode

    @staticmethod
    def _get_wav(playlist: m3u8.M3U8, opening: bool, episode: int) -> tuple[str, float]:
        """
        Downloads and merges audio segments into a single wav file.
        Warn: this method is called in separate subprocesses.
        """
        segments, current_duration = AudioProvider._build_segments_list(playlist, opening)
        wav_path = download_and_merge_parts(episode, segments)
        return wav_path, current_duration

    @staticmethod
    def _build_segments_list(playlist: m3u8.M3U8, opening: bool) -> tuple[list[str], float]:
        """Builds a list of segment URIs based on whether it's an opening or not."""
        current_duration = 0.0
        segments = []

        segment_iter = playlist.segments if opening else reversed(playlist.segments)
        for segment in segment_iter:
            segments.append(not_none(segment.uri)) if opening else segments.insert(0, not_none(segment.uri))
            current_duration += not_none(segment.duration)
            if current_duration >= Config.seconds_to_match:
                break

        return segments, current_duration
