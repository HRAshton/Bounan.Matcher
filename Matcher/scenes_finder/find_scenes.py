import logging
import math
import warnings
from statistics import median
from typing import List, Tuple

import m3u8
from m3u8 import M3U8
from series_intro_recognizer.config import Config as SirConfig
from series_intro_recognizer.processors.audio_files import recognise_from_audio_files_with_offsets

from LoanApi.LoanApi.get_playlist import get_playlist
from LoanApi.LoanApi.models import AvailableVideo
from Matcher.config.Config import Config
from Matcher.models.Interval import Interval
from Matcher.models.Scenes import Scenes
from Matcher.models.VideoKey import VideoKey
from scenes_finder.audio_provider import get_wav_iter, get_truncated_durations

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = SirConfig(series_window=Config.episodes_to_match,
                           save_intermediate_results=False)


def _fix_openings(openings: List[Interval],
                  playlists_and_durations: List[tuple[M3U8, float]],
                  truncated_durations: List[float]) -> List[Interval]:
    """
    Fix openings by extending them to the beginning or prolonging them to the median duration.
    """
    fixed_openings: List[Interval] = []
    zipped = list(zip(openings, truncated_durations, playlists_and_durations))
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


def _fix_endings(endings: List[Interval],
                 playlists_and_durations: List[tuple[M3U8, float]],
                 truncated_durations: List[float]) -> List[Interval]:
    fixed_endings: List[Interval] = []
    zipped = list(zip(endings, truncated_durations, playlists_and_durations))
    for ending, duration, (_, total_duration) in zipped:
        offset = total_duration - duration
        fixed_endings.append(Interval(ending.start + offset, ending.end + offset))

    return fixed_endings


def _get_openings(playlists_and_durations: List[tuple[M3U8, float]]) -> List[Interval]:
    playlists = [playlist for playlist, _ in playlists_and_durations]
    opening_iter = get_wav_iter(playlists, True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lib_openings = recognise_from_audio_files_with_offsets(opening_iter, DEFAULT_CONFIG)
        openings = [Interval(opening.start, opening.end) for opening in lib_openings]

    truncated_durations = get_truncated_durations()
    fixed_openings: List[Interval] = _fix_openings(openings, playlists_and_durations, truncated_durations)

    return fixed_openings


def _get_endings(playlists_and_durations: List[tuple[M3U8, float]]) -> List[Interval]:
    playlists = [playlist for playlist, _ in playlists_and_durations[:5]]
    ending_iter = get_wav_iter(playlists, False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lib_endings = recognise_from_audio_files_with_offsets(ending_iter, DEFAULT_CONFIG)
        endings = [Interval(ending.start, ending.end) for ending in lib_endings]

    truncated_durations = get_truncated_durations()
    fixed_endings: List[Interval] = _fix_endings(endings, playlists_and_durations, truncated_durations)

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


def _get_playlist_and_duration(video: AvailableVideo) -> Tuple[m3u8.M3U8, float] | None:
    playlist_content = get_playlist(video)
    playlist = m3u8.loads(playlist_content)
    if not playlist.segments:
        logger.warning(f"Skipping video {video.id} because it has no segments")
        return None

    total_duration = sum([segment.duration for segment in playlist.segments])
    if total_duration < 2 * Config.seconds_to_match:
        logger.warning(f"Skipping video {video.id} because it's too short ({total_duration}s)")
        return None

    return playlist, total_duration

def find_scenes(videos_to_process: List[AvailableVideo]) -> List[Tuple[VideoKey, Scenes]] | None:
    logger.debug("Processing videos")

    playlists_and_durations = [_get_playlist_and_duration(video)
                               for video in videos_to_process]
    if None in playlists_and_durations:
        return None

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
