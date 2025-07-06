import pytest
import requests
import os
import sys
import logging
from unittest import mock


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stream_consumer import consumer as consumer_script


@pytest.fixture(autouse=True)
def mock_django_settings():
    with mock.patch("django.conf.settings") as mock_settings:
        mock_settings.CASHCOG_STREAM_URL = "http://mock-stream-url.com"
        mock_settings.DEFAULT_STREAM_TYPE = "expense"
        yield mock_settings


@pytest.fixture(autouse=True)
def mock_django_setup():
    with mock.patch("django.setup") as mock_setup:
        yield mock_setup


# Mock load_dotenv to prevent loading actual .env during tests
@pytest.fixture(autouse=True)
def mock_load_dotenv():
    with mock.patch("dotenv.load_dotenv") as mock_load:
        yield mock_load


# Fixture to capture log messages
@pytest.fixture
def caplog_for_consumer(caplog):
    # Set the logging level for the consumer's logger
    caplog.set_level(logging.INFO, logger="stream_consumer.consumer")
    return caplog


def test_setup_django_calls_django_setup(mock_django_setup, mock_django_settings):
    """
    Test that setup_django correctly calls django.setup() and sets environment variables.
    """
    # Ensure environment variable is not set before the call to test setdefault
    if "DJANGO_SETTINGS_MODULE" in os.environ:
        del os.environ["DJANGO_SETTINGS_MODULE"]

    consumer_script.setup_django()

    mock_django_setup.assert_called_once()
    assert os.environ["DJANGO_SETTINGS_MODULE"] == "xcnt.settings"


def test_setup_django_handles_error(mock_django_setup, caplog_for_consumer):
    """
    Test that setup_django handles exceptions during django.setup().
    """
    mock_django_setup.side_effect = Exception("Django setup failed")

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        consumer_script.setup_django()

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


def test_configure_logging_setup(caplog_for_consumer):
    """
    Test that configure_logging sets up the logger correctly.
    """
    logger = consumer_script.configure_logging()

    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert logger.name == "stream_consumer.consumer"

    # Test idempotency: calling again should not add more handlers
    consumer_script.configure_logging()
    assert len(logger.handlers) == 1


@mock.patch("stream_consumer.consumer.time.sleep", return_value=None)
@mock.patch("stream_consumer.consumer.requests.get")
@mock.patch("stream_consumer.consumer.generate_json_objects")
@mock.patch("stream_consumer.consumer.settings")  # ✅ patch actual settings import
def test_run_stream_consumer_success(
    mock_settings,
    mock_generate_json_objects,
    mock_requests_get,
    mock_sleep,
    caplog_for_consumer,
):
    mock_settings.CASHCOG_STREAM_URL = "http://mock-stream-url.com"
    mock_settings.DEFAULT_STREAM_TYPE = "expense"

    mock_event_processor = mock.Mock(spec=consumer_script.AbstractEventProcessor)

    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value.__enter__.return_value = mock_response

    events = [
        {"uuid": "event1", "data": "value1"},
        {"uuid": "event2", "data": "value2"},
    ]
    mock_generate_json_objects.return_value = iter(events)

    consumer_script.run_stream_consumer(
        mock_event_processor, consumer_script.configure_logging(), stop_after=2
    )

    mock_requests_get.assert_called_once_with(
        "http://mock-stream-url.com", stream=True, timeout=(5, 10)
    )

    mock_generate_json_objects.assert_called_once_with(mock_response)
    mock_event_processor.process_event.assert_has_calls(
        [
            mock.call(events[0]),
            mock.call(events[1]),
        ]
    )

    assert "Successfully connected to the stream." in caplog_for_consumer.text
    assert (
        "Attempting to connect to stream at: http://mock-stream-url.com for type: 'expense'"
        in caplog_for_consumer.text
    )


@mock.patch("stream_consumer.consumer.time.sleep", return_value=None)
@mock.patch("requests.get")
def test_run_stream_consumer_request_exception(
    mock_requests_get, mock_sleep, caplog_for_consumer
):
    """
    Test handling of requests.exceptions.RequestException during stream connection.
    """
    mock_event_processor = mock.Mock(spec=consumer_script.AbstractEventProcessor)
    mock_requests_get.side_effect = requests.exceptions.RequestException(
        "Connection error"
    )

    # We expect the loop to continue, so we'll run it a few times and then break
    # by raising a side effect on sleep after a few calls.
    mock_sleep.side_effect = [None, None, StopIteration]  # Sleep twice, then stop

    with pytest.raises(StopIteration):
        consumer_script.run_stream_consumer(
            mock_event_processor, consumer_script.configure_logging()
        )

    assert (
        "Request Exception occurred during stream connection: Connection error. Retrying in 5 seconds..."
        in caplog_for_consumer.text
    )
    assert mock_requests_get.call_count == 3  # Called three times before StopIteration
    assert mock_sleep.call_count == 3  # Sleep called three times


@mock.patch("stream_consumer.consumer.time.sleep", return_value=None)
@mock.patch("requests.get")
def test_run_stream_consumer_generic_exception_on_connect(
    mock_requests_get, mock_sleep, caplog_for_consumer
):
    """
    Test handling of generic exceptions during stream connection.
    """
    mock_event_processor = mock.Mock(spec=consumer_script.AbstractEventProcessor)
    mock_requests_get.side_effect = ValueError("Something went wrong")

    mock_sleep.side_effect = [None, None, StopIteration]

    with pytest.raises(StopIteration):
        consumer_script.run_stream_consumer(
            mock_event_processor, consumer_script.configure_logging()
        )

    assert (
        "Unexpected error during stream consumption: Something went wrong. Retrying in 5 seconds..."
        in caplog_for_consumer.text
    )
    assert mock_requests_get.call_count == 3
    assert mock_sleep.call_count == 3


@mock.patch("stream_consumer.consumer.configure_logging")
@mock.patch("stream_consumer.consumer.StreamProcessorFactory.get_processor")
@mock.patch("stream_consumer.consumer.run_stream_consumer")
def test_main_success(
    mock_run_stream_consumer,
    mock_get_processor,
    mock_configure_logging,
    mock_django_settings,  # Ensure settings are mocked for settings.DEFAULT_STREAM_TYPE
):
    """
    Test successful execution of the main function.
    """
    mock_logger = mock.Mock(spec=logging.Logger)
    mock_configure_logging.return_value = mock_logger
    mock_processor = mock.Mock(spec=consumer_script.AbstractEventProcessor)
    mock_get_processor.return_value = mock_processor

    consumer_script.main()

    mock_configure_logging.assert_called_once()
    mock_get_processor.assert_called_once_with(
        stream_type=mock_django_settings.DEFAULT_STREAM_TYPE,
        logger_instance=mock_logger,
    )
    mock_run_stream_consumer.assert_called_once_with(mock_processor, mock_logger)


@mock.patch("stream_consumer.consumer.configure_logging")
@mock.patch("stream_consumer.consumer.StreamProcessorFactory.get_processor")
@mock.patch("sys.exit")  # Mock sys.exit to prevent actual exit
def test_main_processor_init_failure(
    mock_sys_exit, mock_get_processor, mock_configure_logging, caplog_for_consumer
):
    """
    Test that main handles ValueError during processor initialization.
    """
    mock_logger = mock.Mock(spec=logging.Logger)
    mock_configure_logging.return_value = mock_logger
    mock_get_processor.side_effect = ValueError("Unknown stream type")

    consumer_script.main()

    mock_configure_logging.assert_called_once()
    mock_get_processor.assert_called_once()
    mock_logger.critical.assert_called_once_with(
        "Failed to initialize stream consumer: Unknown stream type"
    )
    mock_sys_exit.assert_called_once_with(1)
