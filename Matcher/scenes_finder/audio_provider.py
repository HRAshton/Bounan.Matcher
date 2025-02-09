import logging
import os
from typing import List, Tuple, Iterator

import m3u8

from Matcher.config.config import Config
from Matcher.scenes_finder.audio_merger import download_and_merge_parts
from Matcher.helpers.pre_request import pre_request, get_result, init_pre_request_queue

DELETE_TEMP_FILES = True

logger = logging.getLogger(__name__)

file_path_to_delete: str | None = None
truncated_durations_per_episode: List[float] | None = None


def get_wav_iter(playlists: List[m3u8.M3U8], opening: bool) -> Iterator[Tuple[str, float, float]]:
    global file_path_to_delete, truncated_durations_per_episode

    truncated_durations_per_episode = []
    if len(playlists) < 2:
        return

    init_pre_request_queue()
    pre_request(0, _get_wav, playlists[0], opening, 0)

    for i, playlist in enumerate(playlists):
        if file_path_to_delete is not None and DELETE_TEMP_FILES and os.path.exists(file_path_to_delete):
            os.remove(file_path_to_delete)

        wav_path, segments_duration = get_result(i)
        if i + 1 < len(playlists):
            pre_request(i + 1, _get_wav, playlists[i + 1], opening, i + 1)

        truncated_duration = min(segments_duration, Config.seconds_to_match)
        offset = 0 if opening else max(segments_duration - Config.seconds_to_match, 0)

        truncated_durations_per_episode.append(truncated_duration)
        file_path_to_delete = wav_path

        yield wav_path, offset, truncated_duration


def get_truncated_durations() -> List[float]:
    global truncated_durations_per_episode
    assert truncated_durations_per_episode
    return truncated_durations_per_episode


def _get_wav(playlist: m3u8.M3U8, opening: bool, episode: int) -> Tuple[str, float]:
    segments, current_duration = _build_segments_list(playlist, opening)
    wav_path = download_and_merge_parts(episode, segments)
    return wav_path, current_duration


def _build_segments_list(playlist: m3u8.M3U8, opening: bool) -> Tuple[List[str], float]:
    current_duration = 0
    segments = []
    if opening:
        for segment in playlist.segments:
            segments.append(segment.uri)
            current_duration += segment.duration
            if current_duration >= Config.seconds_to_match:
                break
    else:
        for segment in reversed(playlist.segments):
            segments.insert(0, segment.uri)
            current_duration += segment.duration
            if current_duration >= Config.seconds_to_match:
                break

    return segments, current_duration
