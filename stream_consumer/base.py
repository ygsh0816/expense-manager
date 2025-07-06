from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AbstractEventProcessor(ABC):
    """
    Abstract base class for processing individual stream events.
    Concrete implementations will define specific validation,
    transformation, and persistence logic.
    """

    def __init__(self, logger_instance: logging.Logger = logger):
        self.logger = logger_instance

    @abstractmethod
    def process_event(self, event_data: Dict[str, Any]):
        """
        Processes a single event dictionary.
        This method should handle validation, business logic, and data persistence.
        """
        pass
