import boto3


def get_ssm_parameter(parameter_name: str) -> str:
    """
    Fetches the parameter value from AWS Systems Manager (SSM) Parameter Store.

    :param parameter_name: Name of the parameter to fetch.
    :return: The parameter value.
    """
    ssm_client = boto3.client("ssm")
    response = ssm_client.get_parameter(Name=parameter_name)
    return response['Parameter']['Value']
