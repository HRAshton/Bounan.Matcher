from typing import List

import boto3
import marshmallow_dataclass

from Matcher.AniMenClient.MatcherResponse import MatcherResponse
from Matcher.AniMenClient.VideoScenesResponse import VideoScenesResponse, VideoScenesResponseItem
from Matcher.config import Config
from models.Scenes import Scenes
from models.VideoKey import VideoKey

lambda_client = boto3.client('lambda')


def get_videos_to_match() -> MatcherResponse:
    response = lambda_client.invoke(
        FunctionName=Config.Config.get_series_to_match_lambda_name,
        InvocationType='RequestResponse',
    )
    payload = response['Payload'].read().decode('utf-8')

    schema = marshmallow_dataclass.class_schema(MatcherResponse)()
    matcher_response = schema.loads(payload)

    return matcher_response


def update_video_scenes(data: VideoScenesResponse) -> None:
    schema = marshmallow_dataclass.class_schema(VideoScenesResponse)()
    payload = schema.dumps(data)

    lambda_client.invoke(
        FunctionName=Config.Config.update_video_scenes_lambda_name,
        InvocationType='RequestResponse',
        Payload=payload
    )


def upload_empty_scenes(videos_to_match: List[VideoKey]) -> None:
    data = [VideoScenesResponseItem(video_key=video_key, scenes=Scenes(None, None, None))
            for video_key in videos_to_match]
    update_video_scenes(VideoScenesResponse(items=data))
