import pytest
from uuid import uuid4
from .factories import ExpenseFactory
from expense_manager.models import ApprovalStatus
from expense_manager.services import (
    ExpenseService,
    ExpenseNotFound,
    InvalidStatusError,
    ExpenseAlreadyProcessedError,
)
from expense_manager.schemas import ExpenseOutSchema


@pytest.mark.django_db
def test_get_expenses_no_filter():
    ExpenseFactory()
    ExpenseFactory()
    expenses, total_pages, total_expenses = ExpenseService.get_expenses()
    assert len(expenses) == 2
    assert total_expenses == 2
    assert total_pages == 1


@pytest.mark.django_db
def test_get_expenses_filter_status():
    ExpenseFactory(status=ApprovalStatus.PENDING.value)
    ExpenseFactory(status=ApprovalStatus.APPROVED.value)
    expenses, total_pages, total_expenses = ExpenseService.get_expenses(
        status=ApprovalStatus.PENDING.value
    )
    assert len(expenses) == 1
    assert total_expenses == 1
    assert total_pages == 1
    assert expenses[0].status == ApprovalStatus.PENDING.value


@pytest.mark.django_db
def test_get_expense_by_uuid_success():
    expense = ExpenseFactory()
    retrieved_expense = ExpenseService.get_expense_by_uuid(expense.uuid)
    assert retrieved_expense == expense


@pytest.mark.django_db
def test_get_expense_by_uuid_not_found():
    with pytest.raises(ExpenseNotFound):
        ExpenseService.get_expense_by_uuid(uuid4())


@pytest.mark.django_db
def test_update_expense_status_success():
    expense = ExpenseFactory(status=ApprovalStatus.PENDING.value)
    updated_expense = ExpenseService.update_expense_status(
        expense.uuid, ApprovalStatus.APPROVED.value
    )
    assert updated_expense.status == ApprovalStatus.APPROVED.value


@pytest.mark.django_db
def test_update_expense_status_not_found():
    with pytest.raises(ExpenseNotFound):
        ExpenseService.update_expense_status(uuid4(), ApprovalStatus.APPROVED.value)


@pytest.mark.django_db
def test_update_expense_status_invalid_status():
    expense = ExpenseFactory(status=ApprovalStatus.PENDING.value)
    with pytest.raises(InvalidStatusError):
        ExpenseService.update_expense_status(expense.uuid, "INVALID_STATUS")


@pytest.mark.django_db
def test_update_expense_status_already_processed():
    expense = ExpenseFactory(status=ApprovalStatus.APPROVED.value)
    with pytest.raises(ExpenseAlreadyProcessedError):
        ExpenseService.update_expense_status(
            expense.uuid, ApprovalStatus.DECLINED.value
        )
