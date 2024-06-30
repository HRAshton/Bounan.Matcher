from Common.py_generated.bounan_common.models.interval import Interval
from Common.py_generated.bounan_common.models.matcher_result_request import MatcherResultRequest
from Common.py_generated.bounan_common.models.matcher_result_request_item import MatcherResultRequestItem
from Common.py_generated.bounan_common.models.scenes import Scenes
from Common.py_generated.bounan_common.models.video_key import VideoKey


def create_video_key(my_anime_list_id: int, dub: str, episode: int) -> VideoKey:
    return VideoKey(my_anime_list_id=my_anime_list_id, dub=dub, episode=episode)


def create_interval(start: float, end: float) -> Interval:
    return Interval(start=start, end=end)


def create_scenes(opening: Interval | None, ending: Interval | None, scene_after_ending: Interval | None) -> Scenes:
    return Scenes(opening=opening.to_dict() if opening else None,
                  ending=ending.to_dict() if ending else None,
                  scene_after_ending=scene_after_ending.to_dict() if scene_after_ending else None)


def create_matcher_result_request_item(my_anime_list_id: int,
                                       dub: str,
                                       episode: int,
                                       scenes: Scenes) -> MatcherResultRequestItem:
    return MatcherResultRequestItem(my_anime_list_id=my_anime_list_id,
                                    dub=dub,
                                    episode=episode,
                                    scenes=scenes.to_dict())


def create_matcher_result_request(items: list[MatcherResultRequestItem]) -> MatcherResultRequest:
    return MatcherResultRequest(items=map(lambda item: item.to_dict(), items))
