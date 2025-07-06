import os
import sys
import logging
import time
from typing import Optional
import django
from dotenv import load_dotenv
import requests

load_dotenv()


def setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xcnt.settings")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        django.setup()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to set up Django. Error: {e}", file=sys.stderr)
        sys.exit(1)


setup_django()
from django.conf import settings
from stream_consumer.base import AbstractEventProcessor
from stream_consumer.factory import StreamProcessorFactory  # Import the factory
from stream_consumer.stream_utils import generate_json_objects


def configure_logging():
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def run_stream_consumer(
    event_processor: AbstractEventProcessor,
    logger: logging.Logger,
    stop_after: Optional[int] = None,
):
    """
    Connects to the configured stream and delegates event processing.
    """
    logger.info(
        f"Attempting to connect to stream at: {settings.CASHCOG_STREAM_URL} for type: '{settings.DEFAULT_STREAM_TYPE}'"
    )
    attempts = 0  # Track connection attempts for tests
    while True:
        if stop_after is not None:
            attempts += 1
            if attempts >= stop_after:
                break
        try:
            with requests.get(
                settings.CASHCOG_STREAM_URL, stream=True, timeout=(5, 10)
            ) as response:
                response.raise_for_status()
                logger.info("Successfully connected to the stream.")

                for event_data in generate_json_objects(response):
                    try:
                        event_processor.process_event(event_data)
                    except Exception as e:
                        logger.exception(
                            f"Unhandled error during event processing loop for event: {event_data.get('uuid', 'N/A')}: {e}"
                        )

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Request Exception occurred during stream connection: {e}. Retrying in 5 seconds..."
            )
            time.sleep(5)
        except Exception as e:
            logger.exception(
                f"Unexpected error during stream consumption: {e}. Retrying in 5 seconds..."
            )
            time.sleep(5)


def main():
    logger = configure_logging()

    try:
        processor = StreamProcessorFactory.get_processor(
            stream_type=settings.DEFAULT_STREAM_TYPE, logger_instance=logger
        )
        run_stream_consumer(processor, logger)
    except ValueError as e:
        logger.critical(f"Failed to initialize stream consumer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
