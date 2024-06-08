from dataclasses import dataclass, field

from Matcher.models.Scenes import Scenes
from Matcher.models.VideoKey import VideoKey


@dataclass
class VideoScenesResponseItem:
    video_key: VideoKey = field(metadata={'data_key': 'VideoKey'})
    scenes: Scenes = field(metadata={'data_key': 'Scenes'})


@dataclass
class VideoScenesResponse:
    items: list[VideoScenesResponseItem] = field(metadata={'data_key': 'Items'})
