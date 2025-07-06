import time
import logging
from typing import Dict, Any

from django.db import IntegrityError, transaction
from django.conf import settings

from stream_consumer.base import AbstractEventProcessor
from expense_manager.models import Expense, Employee, ApprovalStatus
from expense_manager.schemas import SingleExpenseSchema

logger = logging.getLogger(__name__)


class ExpenseEventProcessor(AbstractEventProcessor):
    """
    Concrete processor for Cashcog expense stream events.
    Handles validation, employee updates, and expense creation.
    """

    def __init__(self, logger_instance: logging.Logger = logger):
        super().__init__(logger_instance)
        self.max_retries = getattr(settings, "STREAM_PROCESSING_MAX_RETRIES", 3)

    def process_event(self, event_data: Dict[str, Any]):
        retries = 0
        while retries < self.max_retries:
            try:
                validated_data = SingleExpenseSchema(**event_data)
                self.logger.debug(f"Validated data for UUID: {validated_data.uuid}")
                print(validated_data)
                with transaction.atomic():
                    employee, created = Employee.objects.get_or_create(
                        uuid=validated_data.employee.uuid,
                        defaults={
                            "first_name": validated_data.employee.first_name,
                            "last_name": validated_data.employee.last_name,
                        },
                    )
                    if not created:
                        if (
                            employee.first_name != validated_data.employee.first_name
                            or employee.last_name != validated_data.employee.last_name
                        ):
                            employee.first_name = validated_data.employee.first_name
                            employee.last_name = validated_data.employee.last_name
                            employee.save(update_fields=["first_name", "last_name"])

                    if Expense.objects.filter(uuid=validated_data.uuid).exists():
                        self.logger.warning(
                            f"Expense with UUID {validated_data.uuid} already exists. Skipping."
                        )
                        return
                    expense = Expense.objects.create(
                        uuid=validated_data.uuid,
                        description=validated_data.description,
                        created_at=validated_data.created_at,
                        amount=float(validated_data.amount),
                        currency=validated_data.currency,
                        employee=employee,
                        status=ApprovalStatus.PENDING.value,
                    )
                    self.logger.info(
                        f"Successfully saved expense: {expense.uuid} for employee {employee.first_name} {employee.last_name}"
                    )
                    return

            except IntegrityError:
                self.logger.warning(
                    f"IntegrityError: Expense with UUID {event_data.get('uuid')} likely already exists. Skipping."
                )
                return
            except Exception as e:
                self.logger.exception(
                    f"Error processing event {event_data.get('uuid')}: {e}. Retry {retries + 1}/{self.max_retries}"
                )
                retries += 1
                time.sleep(2)

        self.logger.error(
            f"Failed to process event {event_data.get('uuid')} after {self.max_retries} retries. "
            "Consider sending to a Dead-Letter Queue for manual review or reprocessing."
        )
