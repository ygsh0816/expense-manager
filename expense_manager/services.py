import logging
from typing import List, Optional, Tuple
from uuid import UUID

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import QuerySet
from xcnt import exceptions

from .models import Expense, ApprovalStatus

logger = logging.getLogger(__name__)


class ExpenseServiceError(exceptions.HttpException):
    """Base exception for ExpenseService errors."""

    error_type = "expense_service_error"
    error_message = "An error occurred while processing the expense."


class ExpenseNotFound(exceptions.HttpException):
    """Raised when an expense with the given UUID is not found."""

    error_type = "expense_not_found"
    error_template = "Expense with UUID: {uuid} not found."

    def __init__(self, uuid: str) -> None:
        super().__init__(uuid)


class InvalidStatusError(exceptions.HttpException):
    """Raised when an invalid status value is provided."""

    error_type = "invalid_status"
    error_template = (
        "Invalid status provided: {status}. Must be PENDING, APPROVED, or DECLINED."
    )

    def __init__(self, status: str) -> None:
        super().__init__(status)


class ExpenseAlreadyProcessedError(exceptions.HttpException):
    error_type = "expense_already_processed"
    error_template = "Expense with UUID: {uuid} has already been processed."

    def __init__(self, uuid: str) -> None:
        super().__init__(uuid)


class ExpenseService:
    """
    Service layer for managing Expense objects.
    Encapsulates business logic and database access.
    """

    @staticmethod
    def get_expenses(
        status: Optional[str] = None,
        employee_uuid: Optional[UUID] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        currency: Optional[str] = None,
        search_description: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Expense], int, int]:
        """
        Retrieves a list of expenses based on provided filters and pagination.
        Returns a tuple containing:
            - A list of Expense objects for the current page.
            - The total number of pages available.
            - The total number of expenses matching the filters.
        """

        expenses_queryset: QuerySet[Expense] = Expense.objects.all()
        filters: dict[str, str | UUID | float] = {}

        if status:
            # Validate status against allowed choices in the model
            if status.upper() not in [choice.value for choice in ApprovalStatus]:
                logger.warning(f"Attempted to filter with invalid status: {status}")
                raise InvalidStatusError(
                    f"Invalid status provided: '{status}'. Must be PENDING, APPROVED, or DECLINED."
                )
            filters["status"] = status.upper()

        if employee_uuid:
            filters["uuid"] = employee_uuid

        if min_amount is not None:
            filters["amount__gte"] = min_amount

        if max_amount is not None:
            filters["amount__lte"] = max_amount

        if currency:
            filters["currency__iexact"] = currency

        if search_description:
            filters["description__icontains"] = search_description

        # Apply all collected filters to the queryset at once
        expenses_queryset = expenses_queryset.filter(**filters)

        # Apply pagination using Django's Paginator
        paginator = Paginator(expenses_queryset, page_size)
        total_expenses = paginator.count
        total_pages = paginator.num_pages

        try:
            expenses_page = paginator.page(page)
        except PageNotAnInteger:
            logger.info(
                f"Page number '{page}' is not an integer. Delivering first page."
            )
            expenses_page = paginator.page(1)
        except EmptyPage:
            logger.info(
                f"Page number '{page}' is out of range. Delivering last page ({paginator.num_pages})."
            )
            expenses_page = paginator.page(paginator.num_pages)

        paginated_expenses = list(expenses_page.object_list)

        logger.info(
            f"Retrieved {len(paginated_expenses)} expenses (page {expenses_page.number} of {total_pages}, total {total_expenses}) with filters."
        )
        return paginated_expenses, total_pages, total_expenses

    @staticmethod
    def get_expense_by_uuid(expense_uuid: UUID) -> Expense:
        """
        Retrieves a single expense by its UUID.
        Raises ExpenseNotFound if the expense does not exist.
        """
        try:
            expense = Expense.objects.get(uuid=expense_uuid)
            logger.info(f"Retrieved expense: {expense_uuid}")
            return expense
        except Expense.DoesNotExist:
            logger.warning(f"Expense with UUID {expense_uuid} not found.")
            raise ExpenseNotFound(uuid=str(expense_uuid))

    @staticmethod
    def update_expense_status(expense_uuid: UUID, new_status: str) -> Expense:
        """
        Updates the status of an expense.
        Enforces business rules for status transitions.
        """

        try:
            expense = Expense.objects.get(uuid=expense_uuid)
        except Expense.DoesNotExist:
            logger.warning(f"Attempted to update non-existent expense: {expense_uuid}")
            raise ExpenseNotFound(uuid=str(expense_uuid))

        # Validate the new status against allowed update values
        allowed_update_statuses = [
            ApprovalStatus.APPROVED.value,
            ApprovalStatus.DECLINED.value,
        ]
        if new_status.upper() not in allowed_update_statuses:
            logger.warning(
                f"Invalid status update attempted for {expense_uuid}: {new_status}"
            )
            raise InvalidStatusError(status=new_status)

        # Business rule: Only PENDING expenses can be updated
        if expense.status != ApprovalStatus.PENDING.value:
            logger.warning(
                f"Attempted to update non-pending expense {expense_uuid}. Current status: {expense.status}"
            )
            raise ExpenseAlreadyProcessedError(uuid=str(expense_uuid))

        expense.status = new_status.upper()
        expense.save()
        logger.info(f"Updated expense {expense_uuid} status to {new_status}")
        return expense
