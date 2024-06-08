from dataclasses import field, dataclass
from typing import List

from Matcher.models.VideoKey import VideoKey


@dataclass
class MatcherResponse:
    videos_to_match: List[VideoKey] = field(metadata={'data_key': 'VideosToMatch'})
