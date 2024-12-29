import logging

import watchtower

from Matcher.config.Config import Config

fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def setup_logging() -> None:
    cloudwatch_handler = watchtower.CloudWatchLogHandler(log_group_name=Config.log_group_name,
                                                         create_log_group=False,
                                                         log_stream_name=Config.log_group_name,
                                                         level=Config.log_level,
                                                         send_interval=10)
    formatter = logging.Formatter(fmt)
    cloudwatch_handler.setFormatter(formatter)

    logging.basicConfig(level=Config.log_level,
                        format=fmt,
                        handlers=[
                            logging.StreamHandler(),
                            cloudwatch_handler,
                        ])
