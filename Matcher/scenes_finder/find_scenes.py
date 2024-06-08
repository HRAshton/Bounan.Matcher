import logging
import math
import os
from statistics import median
from typing import List, Tuple, Iterator

import m3u8
from m3u8 import M3U8
from series_intro_recognizer.config import Config as SirConfig
from series_intro_recognizer.processors.audio_files import recognise_from_audio_files

from LoanApi.LoanApi.get_playlist import get_playlist
from LoanApi.LoanApi.models import AvailableVideo
from Matcher.config.Config import Config
from Matcher.models.Interval import Interval
from Matcher.models.Scenes import Scenes
from Matcher.models.VideoKey import VideoKey
from Matcher.scenes_finder.audio_merger import download_and_merge_parts

logger = logging.getLogger(__name__)

PATH_TEMP_DIR = os.path.join(Config.temp_dir, 'parts')
DEFAULT_CONFIG = SirConfig(series_window=Config.episodes_to_match,
                           save_intermediate_results=False)

file_path_to_delete: str | None = None
truncated_durations_per_episode: List[float] | None = None


def _get_playlist_and_duration(video: AvailableVideo) -> Tuple[m3u8.M3U8, float]:
    playlist_content = get_playlist(video)
    playlist = m3u8.loads(playlist_content)
    if not playlist.segments:
        raise SystemExit(f"Skipping video {video.id} because it has no segments")

    total_duration = sum([segment.duration for segment in playlist.segments])
    if total_duration < 2 * Config.seconds_to_match:
        raise SystemExit(f"Skipping video {video.id} because it's too short ({total_duration}s)")

    return playlist, total_duration


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


def _get_wav(playlist: m3u8.M3U8, opening: bool, episode: int) -> Tuple[str, float]:
    segments, current_duration = _build_segments_list(playlist, opening)
    wav_path = download_and_merge_parts(episode, segments)
    return wav_path, current_duration


def _get_wav_iter(playlists: List[m3u8.M3U8], opening: bool) -> Iterator[str]:
    global file_path_to_delete, truncated_durations_per_episode
    truncated_durations_per_episode = []
    for i, playlist in enumerate(playlists):
        if file_path_to_delete is not None:
            os.remove(file_path_to_delete)

        wav_path, truncated_duration = _get_wav(playlist, opening, i)
        truncated_durations_per_episode.append(truncated_duration)
        file_path_to_delete = wav_path
        yield wav_path


def _fix_openings(openings: List[Interval], playlists_and_durations: List[tuple[M3U8, float]]) -> List[Interval]:
    """
    Fix openings by extending them to the beginning or prolonging them to the median duration.
    """
    fixed_openings: List[Interval] = []
    zipped = list(zip(openings, truncated_durations_per_episode, playlists_and_durations))
    median_duration = median([opening.end - opening.start for opening, _, _ in zipped])
    for opening, duration, (_, total_duration) in zipped:
        if opening.start < Config.scene_after_opening_threshold_secs:
            # If the beginning of the opening is close to the beginning of the video, extend it.
            fixed_openings.append(Interval(0, opening.end))
        elif abs(total_duration - opening.end) < Config.scene_after_opening_threshold_secs:
            # If the end of the opening is close to the end of the video, extend it to the average duration.
            fixed_openings.append(Interval(opening.start, opening.start + median_duration))
        else:
            fixed_openings.append(opening)

    return fixed_openings


def _get_openings(playlists_and_durations: List[tuple[M3U8, float]]) -> List[Interval]:
    playlists = [playlist for playlist, _ in playlists_and_durations]
    opening_iter = _get_wav_iter(playlists, True)
    # noinspection PyTypeChecker
    openings: List[Interval] = recognise_from_audio_files(opening_iter, DEFAULT_CONFIG)

    fixed_openings: List[Interval] = _fix_openings(openings, playlists_and_durations)

    return fixed_openings


def _get_endings(playlists_and_durations: List[tuple[M3U8, float]]) -> List[Interval]:
    global truncated_durations_per_episode

    playlists = [playlist for playlist, _ in playlists_and_durations]
    ending_iter = _get_wav_iter(playlists, False)
    endings = recognise_from_audio_files(ending_iter, DEFAULT_CONFIG)

    fixed_endings: List[Interval] = []
    zipped = list(zip(endings, truncated_durations_per_episode, playlists_and_durations))
    for endings, duration, (_, total_duration) in zipped:
        offset = total_duration - duration
        fixed_endings.append(Interval(endings[0] + offset, endings[1] + offset))

    return fixed_endings


def _filter_scene(scene: Interval) -> Interval | None:
    return (scene
            if scene is not None and scene.end - scene.start >= Config.min_scene_length_secs
            else None)


def _combine_scenes(opening: Interval, ending: Interval, total_duration: float) -> Scenes:
    new_opening = opening if not math.isnan(opening.start) else None
    new_ending = ending if not math.isnan(ending.start) else None

    scene_after_ending = None
    if new_ending is not None:
        if abs(total_duration - ending.end) > Config.scene_after_opening_threshold_secs:
            scene_after_ending = Interval(ending.end, total_duration)
        else:
            new_ending = Interval(ending.start, total_duration)

    return Scenes(_filter_scene(new_opening),
                  _filter_scene(new_ending),
                  _filter_scene(scene_after_ending))


def find_scenes(videos_to_process: List[AvailableVideo]) -> List[Tuple[VideoKey, Scenes]]:
    logger.debug("Processing videos")

    playlists_and_durations = [_get_playlist_and_duration(video)
                               for video in videos_to_process]

    openings = _get_openings(playlists_and_durations)
    endings = _get_endings(playlists_and_durations)

    all_scenes = []
    zipped = list(zip(videos_to_process, playlists_and_durations, openings, endings))
    for video, (_, total_duration), opening, ending in zipped:
        """
        1. Set field to None if there is no scene.
        2. Extend scenes to the beginning and the end of the video.
        3. Calculate the scene after the ending.
        """
        scenes = _combine_scenes(opening, ending, total_duration)

        video_key = VideoKey(video.my_anime_list_id, video.dub, video.episode)
        all_scenes.append((video_key, scenes))

    return all_scenes
