import logging
from typing import Dict, Type

from stream_consumer.base import AbstractEventProcessor
from stream_consumer.expense_processor import ExpenseEventProcessor

logger = logging.getLogger(__name__)


PROCESSOR_REGISTRY: Dict[str, Type[AbstractEventProcessor]] = {
    "expense": ExpenseEventProcessor,
    # We can add other processors here as we create them:
    # "order": OrderEventProcessor,
    # "inventory": InventoryEventProcessor,
}


class StreamProcessorFactory:
    @staticmethod
    def get_processor(
        stream_type: str, logger_instance: logging.Logger = logger
    ) -> AbstractEventProcessor:
        """
        Factory method to create and return an instance of the appropriate
        AbstractEventProcessor based on the given stream_type.

        Args:
            stream_type (str): The identifier for the type of stream (e.g., "expense").
            logger_instance (logging.Logger): The logger to pass to the processor.

        Returns:
            AbstractEventProcessor: An instance of the requested stream processor.

        Raises:
            ValueError: If an unknown stream_type is provided.
        """
        processor_class = PROCESSOR_REGISTRY.get(stream_type)
        if not processor_class:
            raise ValueError(
                f"Unknown stream type: '{stream_type}'. "
                f"Available types: {', '.join(PROCESSOR_REGISTRY.keys())}"
            )

        logger_instance.info(f"Creating processor for stream type: '{stream_type}'")
        return processor_class(logger_instance=logger_instance)
