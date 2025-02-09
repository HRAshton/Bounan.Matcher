import logging
import os
from typing import Iterator

import m3u8

from Matcher.config.config import Config
from Matcher.helpers.not_none import not_none
from Matcher.helpers.pre_request import PreRequestQueue
from Matcher.scenes_finder.audio_merger import download_and_merge_parts

DELETE_TEMP_FILES = True

logger = logging.getLogger(__name__)

file_path_to_delete: str | None = None
truncated_durations_per_episode: list[float] | None = None


def get_wav_iter(playlists: list[m3u8.M3U8], opening: bool) -> Iterator[tuple[str, float, float]]:
    global file_path_to_delete, truncated_durations_per_episode

    truncated_durations_per_episode = []
    if len(playlists) < 2:
        return

    config_dict = Config.export()
    with PreRequestQueue[[m3u8.M3U8, bool, int], tuple[str, float]](config_dict) as queue:
        queue.pre_request(0, _get_wav, playlists[0], opening, 0)

        for i, playlist in enumerate(playlists):
            if file_path_to_delete is not None and DELETE_TEMP_FILES and os.path.exists(file_path_to_delete):
                os.remove(file_path_to_delete)

            wav_path, segments_duration = queue.pop_result(i)
            if i + 1 < len(playlists):
                # Start downloading next episode in parallel in advance
                queue.pre_request(i + 1, _get_wav, playlists[i + 1], opening, i + 1)

            truncated_duration = min(segments_duration, Config.seconds_to_match)
            offset = 0 if opening else max(segments_duration - Config.seconds_to_match, 0)

            truncated_durations_per_episode.append(truncated_duration)
            file_path_to_delete = wav_path

            yield wav_path, offset, truncated_duration


def get_truncated_durations() -> list[float]:
    global truncated_durations_per_episode
    assert truncated_durations_per_episode
    return truncated_durations_per_episode


def _get_wav(playlist: m3u8.M3U8,
             opening: bool,
             episode: int) -> tuple[str, float]:
    segments, current_duration = _build_segments_list(playlist, opening)
    wav_path = download_and_merge_parts(episode, segments)
    return wav_path, current_duration


def _build_segments_list(playlist: m3u8.M3U8, opening: bool) -> tuple[list[str], float]:
    current_duration = .0
    segments: list[str] = []
    if opening:
        for segment in playlist.segments:
            segments.append(not_none(segment.uri))
            current_duration += not_none(segment.duration)
            if current_duration >= Config.seconds_to_match:
                break
    else:
        for segment in reversed(playlist.segments):
            segments.insert(0, not_none(segment.uri))
            current_duration += not_none(segment.duration)
            if current_duration >= Config.seconds_to_match:
                break

    return segments, current_duration
