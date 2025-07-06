from ninja import Schema
from datetime import datetime
from uuid import UUID
from typing import List


class EmployeeSchema(Schema):
    uuid: UUID
    first_name: str
    last_name: str


class ExpenseUpdateSchema(Schema):
    status: str  # Will be validated to be 'APPROVED' or 'DECLINED'


class ExpenseOutSchema(Schema):
    uuid: UUID
    description: str
    created_at: datetime
    amount: float
    currency: str
    employee_uuid: UUID
    status: str

    @classmethod
    def from_domain(cls, expense):
        return cls(
            uuid=expense.uuid,
            description=expense.description,
            created_at=expense.created_at,
            amount=expense.amount,
            currency=expense.currency,
            employee_uuid=expense.employee.uuid,
            status=expense.status,
        )


class SingleExpenseSchema(Schema):
    uuid: UUID
    description: str
    created_at: datetime
    amount: int  # Amount is int in the example payload, convert to float for storage
    currency: str
    employee: EmployeeSchema


class PaginatedExpenseOutSchema(Schema):
    page: int
    limit: int
    total: int
    count: int
    results: List[ExpenseOutSchema]

    @classmethod
    def from_domain(cls, expenses, total_pages, total_expenses, page, page_size):
        expense_list = [ExpenseOutSchema.from_domain(expense) for expense in expenses]
        return cls(
            page=page,
            limit=page_size,
            total=total_expenses,
            count=len(expense_list),
            results=expense_list,
        )
