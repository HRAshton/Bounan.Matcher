import logging
import time

import boto3

from Matcher.config.config import Config

logger = logging.getLogger(__name__)


def wait_for_notification():
    """
    Wait for a notification from the SQS queue
    """

    last_operating_log_time = time.time()
    client = boto3.client('sqs')

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

        if time.time() - last_operating_log_time > 60 / Config.operating_log_rate_per_minute:
            logger.info("Waiting for new messages...")
            last_operating_log_time = time.time()

        time.sleep(1)
