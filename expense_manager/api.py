import logging
from typing import Optional
from uuid import UUID
from ninja import schema

from ninja import Router, Query


from .schemas import ExpenseOutSchema, ExpenseUpdateSchema, PaginatedExpenseOutSchema
from .services import (
    ExpenseService,
    ExpenseNotFound,
    InvalidStatusError,
    ExpenseAlreadyProcessedError,
)

logger = logging.getLogger(__name__)

router = Router()


@router.get("/", response={200: PaginatedExpenseOutSchema})
def list_expenses(
    request,
    status: Optional[str] = Query(
        None, description="Filter by approval status (PENDING, APPROVED, DECLINED)"
    ),
    employee_uuid: Optional[UUID] = Query(None, description="Filter by employee UUID"),
    min_amount: Optional[float] = Query(None, description="Filter by minimum amount"),
    max_amount: Optional[float] = Query(None, description="Filter by maximum amount"),
    currency: Optional[str] = Query(
        None, description="Filter by currency (case-insensitive)"
    ),
    search_description: Optional[str] = Query(
        None, description="Search description (case-insensitive contains)"
    ),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
) -> tuple[int, PaginatedExpenseOutSchema]:
    """
    Retrieves a list of expenses with optional filtering and pagination.
    """

    expenses, total_pages, total_expenses = ExpenseService.get_expenses(
        status=status,
        employee_uuid=employee_uuid,
        min_amount=min_amount,
        max_amount=max_amount,
        currency=currency,
        search_description=search_description,
        page=page,
        page_size=page_size,
    )
    # Use from_domain to convert Expense model instances to ExpenseOutSchema instances
    response = PaginatedExpenseOutSchema.from_domain(
        expenses, total_pages, total_expenses, page, page_size
    )
    return 200, response


@router.get(
    "/{expense_uuid}", response={200: ExpenseOutSchema, 404: ExpenseNotFound.Schema}
)
def get_expense(
    request, expense_uuid: UUID
) -> tuple[int, ExpenseOutSchema | schema.Schema]:
    """
    Retrieves a single expense by its UUID.
    """
    try:
        expense = ExpenseService.get_expense_by_uuid(expense_uuid)
        return 200, ExpenseOutSchema.from_domain(expense)
    except ExpenseNotFound as e:
        logger.error(f"API Error: Expense not found - {e}")
        return 404, e.to_schema()


@router.put(
    "/{expense_uuid}",
    response={
        200: ExpenseOutSchema,
        404: ExpenseNotFound.Schema,
        400: InvalidStatusError.Schema,
        409: ExpenseAlreadyProcessedError.Schema,
    },
)
def update_expense_status(
    request, expense_uuid: UUID, payload: ExpenseUpdateSchema
) -> tuple[int, ExpenseOutSchema | schema.Schema]:
    """
    Updates the status of an expense (approve or decline).
    """
    try:
        updated_expense = ExpenseService.update_expense_status(
            expense_uuid=expense_uuid, new_status=payload.status
        )
        return 200, ExpenseOutSchema.from_domain(updated_expense)
    except ExpenseNotFound as e:
        logger.error(f"API Error: Expense not found for update - {e}")
        return 404, e.to_schema()  # Not Found
    except InvalidStatusError as e:
        logger.error(f"API Error: Invalid status provided for update - {e}")
        return 400, e.to_schema()  # Bad Request
    except ExpenseAlreadyProcessedError as e:
        logger.warning(
            f"API Warning: Attempted to update already processed expense - {e}"
        )
        return 409, e.to_schema()  # Conflict
