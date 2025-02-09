import logging
import traceback
from typing import List, Tuple

from dotenv import load_dotenv
from retry import retry

from Common.py.models import VideoKey, Scenes, MatcherResultRequest, MatcherResultRequestItem
from LoanApi.LoanApi.get_available_videos import get_available_videos
from LoanApi.LoanApi.models import AvailableVideo
from Matcher import SqsClient
from Matcher.AniMenClient import AniMenClient
from Matcher.AniMenClient.AniMenClient import upload_empty_scenes, update_video_scenes
from Matcher.config.config import Config
from Matcher.matcher_logger import setup_logging
from Matcher.scenes_finder.find_scenes import find_scenes

logger = logging.getLogger(__name__)


def _ensure_if_all_videos_for_same_group(videos_to_match: List[VideoKey]) -> None:
    """
    Ensure if all videos are for the same group
    :param videos_to_match: List of videos to match
    :return: True if all videos are for the same group, False otherwise
    """
    my_anime_list_id = videos_to_match[0].my_anime_list_id
    dub = videos_to_match[0].dub

    for video in videos_to_match:
        if video.my_anime_list_id != my_anime_list_id or video.dub != dub:
            raise ValueError("All videos are not for the same group.")


def _get_videos_to_process(videos_to_match: List[VideoKey]) -> List[AvailableVideo]:
    """
    Get videos to process.
    Returns the same list of videos extended with N more videos before and after
    the videos to match. Where N is the number of consecutive videos to process.
    :param videos_to_match: List of videos to match
    :return: List of videos to process
    """
    assert len(videos_to_match) > 0

    available_videos = get_available_videos(videos_to_match[0].my_anime_list_id,
                                            videos_to_match[0].dub)

    episodes_to_match = Config.episodes_to_match
    indexes_to_process: set[int] = set()
    episode_index_map = {video.episode: idx
                         for idx, video in enumerate(available_videos)}

    for video in videos_to_match:
        if video.episode not in episode_index_map:
            continue

        video_index = episode_index_map[video.episode]
        start_idx = max(0, video_index - episodes_to_match)
        end_idx = min(len(available_videos), video_index + episodes_to_match + 1)

        indexes_to_process.update(set(range(start_idx, end_idx)))

    return [available_videos[i] for i in sorted(indexes_to_process)]


def _get_scenes_to_upload(scenes_by_video: List[Tuple[VideoKey, Scenes]]) -> MatcherResultRequest:
    items = [MatcherResultRequestItem(video_key=video_key, scenes=scenes)
             for video_key, scenes in scenes_by_video]
    return MatcherResultRequest(items=items)


@retry(tries=2, delay=1)
def _process_batch(videos_to_process: List[AvailableVideo]) -> None:
    scenes_by_video = find_scenes(videos_to_process)
    logger.info(f"Scenes by video: {scenes_by_video}")

    scenes_to_upload = _get_scenes_to_upload(scenes_by_video)
    logger.info(f"Scenes to upload ({len(scenes_to_upload.items)}): {scenes_to_upload.items}")

    update_video_scenes(scenes_to_upload)
    logger.info("Scenes uploaded.")


def _process_videos(videos_to_match: List[VideoKey]) -> None:
    logger.info(f"Received {len(videos_to_match)} videos to match: {videos_to_match}.")
    _ensure_if_all_videos_for_same_group(videos_to_match)

    videos_to_process = _get_videos_to_process(videos_to_match)
    if len(videos_to_process) < Config.episodes_to_match:
        logger.info("Not enough videos to process. Waiting for new videos...")
        upload_empty_scenes(videos_to_match)
        return

    unavailable_videos = [video for video in videos_to_match
                          if video.episode not in [v.episode for v in videos_to_process]]
    if len(unavailable_videos) > 0:
        logger.info(f"{len(unavailable_videos)}/{len(videos_to_match)} videos are unavailable: {unavailable_videos}")
        upload_empty_scenes(unavailable_videos)

    logger.info(f"Videos to process ({len(videos_to_process)}): {videos_to_process}")

    # Split videos to process into batches.
    # Last batch should not contain less than Config.batch_size videos.
    batches = [videos_to_process[i:i + Config.batch_size]
               for i in range(0, len(videos_to_process), Config.batch_size)]
    if len(batches) > 1 and len(batches[-1]) < Config.batch_size:
        batches[-2].extend(batches.pop())

    for batch in batches:
        try:
            logger.info(f"Processing batch ({len(batch)}): {batch}")
            _process_batch(batch)
            logger.info("Batch processed.")
        except Exception as e:
            logger.error(f"Error occurred while processing batch: {e}")
            keys = [VideoKey(video.my_anime_list_id, video.dub, video.episode)
                    for video in batch]
            upload_empty_scenes(keys)


def main():
    while True:
        logger.info("Getting the data...")

        videos_to_match: List[VideoKey] = []
        try:
            videos_to_match_res = AniMenClient.get_videos_to_match()
            videos_to_match = videos_to_match_res.videos_to_match
            if len(videos_to_match) == 0:
                logger.info("No videos to match. Waiting for new videos...")
                SqsClient.wait_for_notification()
                continue

            _process_videos(videos_to_match)
        except KeyboardInterrupt:
            logger.error("Shutting down...")
            break
        except Exception as ex:
            logger.error(f"An error occurred: {ex}. "
                         f"{[x for x in traceback.TracebackException.from_exception(ex).format()]}")
            if len(videos_to_match) > 0:
                upload_empty_scenes(videos_to_match)


if __name__ == "__main__":
    load_dotenv()
    Config.initialize_from_env()
    setup_logging()
    logger.info("Starting the data processing...")
    main()
    logger.info("Data processing stopped.")
