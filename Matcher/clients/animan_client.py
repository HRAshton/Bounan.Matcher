import logging

import boto3

from Common.py.models import VideoKey, Scenes, MatcherResponse, MatcherResultRequest, MatcherResultRequestItem
from Matcher.config.config import Config

lambda_client = boto3.client('lambda')
logger = logging.getLogger(__name__)


def get_videos_to_match() -> MatcherResponse:
    response = lambda_client.invoke(
        FunctionName=Config.get_series_to_match_lambda_name,
        InvocationType='RequestResponse',
    )
    payload = response['Payload'].read().decode('utf-8')

    matcher_response = MatcherResponse.schema().loads(payload)  # type: ignore

    return matcher_response


def update_video_scenes(data: MatcherResultRequest) -> None:
    payload = data.to_json()  # type: ignore

    lambda_client.invoke(
        FunctionName=Config.update_video_scenes_lambda_name,
        InvocationType='RequestResponse',
        Payload=payload
    )


def upload_empty_scenes(videos_to_match: list[VideoKey]) -> None:
    logger.info("Uploading empty scenes for videos: %s", videos_to_match)
    data = [MatcherResultRequestItem(video_key, Scenes(None, None, None))
            for video_key in videos_to_match]
    update_video_scenes(MatcherResultRequest(data))
