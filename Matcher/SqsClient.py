import logging
import time

import boto3

from Matcher.config.Config import Config

client = boto3.client('sqs')
logger = logging.getLogger(__name__)


def wait_for_notification():
    """
    Wait for a notification from the SQS queue
    """
    while True:
        messages = client.receive_message(QueueUrl=Config.notification_queue_url,
                                          MaxNumberOfMessages=1,
                                          WaitTimeSeconds=20)

        if 'Messages' in messages:
            client.delete_message(QueueUrl=Config.notification_queue_url,
                                  ReceiptHandle=messages['Messages'][0]['ReceiptHandle'])
            logger.debug("Received messages.")
            break

        logger.debug("No messages received. Waiting for new messages...")
        time.sleep(1)
