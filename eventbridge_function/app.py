import logging

logger = logging.getLogger("parent")
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Received event: %s", event)


