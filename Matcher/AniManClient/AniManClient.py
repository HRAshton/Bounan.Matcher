from typing import List

import boto3

from Common.py_generated.bounan_common.models.matcher_response import MatcherResponse
from Common.py_generated.bounan_common.models.matcher_result_request import MatcherResultRequest
from Common.py_generated.bounan_common.models.video_key import VideoKey
from Matcher.config import Config
from Matcher.model_constructors.constructors import create_matcher_result_request_item, create_scenes, \
    create_matcher_result_request

lambda_client = boto3.client('lambda')


def get_videos_to_match() -> MatcherResponse:
    response = lambda_client.invoke(
        FunctionName=Config.Config.get_series_to_match_lambda_name,
        InvocationType='RequestResponse',
    )
    payload = response['Payload'].read().decode('utf-8')
    matcher_response = MatcherResponse.from_json(payload)

    return matcher_response


def update_video_scenes(data: MatcherResultRequest) -> None:
    payload = data.to_json()

    lambda_client.invoke(
        FunctionName=Config.Config.update_video_scenes_lambda_name,
        InvocationType='RequestResponse',
        Payload=payload
    )


def upload_empty_scenes(videos_to_match: List[VideoKey]) -> None:
    data = [create_matcher_result_request_item(video_key.my_anime_list_id,
                                               video_key.dub,
                                               video_key.episode,
                                               create_scenes(None, None, None))
            for video_key in videos_to_match]
    update_video_scenes(create_matcher_result_request(data))
