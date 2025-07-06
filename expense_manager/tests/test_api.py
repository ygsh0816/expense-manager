# expense_manager/tests/test_api.py
import pytest
from django.urls import reverse
from django.test import Client
import json
from uuid import UUID
from expense_manager.services import (
    ExpenseNotFound,
    InvalidStatusError,
    ExpenseAlreadyProcessedError,
)

import django

django.setup()

# This print statement is good for debugging, but if the error happens BEFORE it,
# it means the problem is in Django's setup, not your test code directly.
# print(f"sys.path in test_api.py: {sys.path}")

# These imports are correct if expense_manager is your app name
from expense_manager.models import ApprovalStatus
from .factories import ExpenseFactory


@pytest.fixture
def api_client():
    """
    Provides a Django test client for making HTTP requests.
    """
    return Client()


@pytest.mark.django_db
def test_list_expenses_no_filter(api_client):
    """
    Tests fetching a list of expenses without any filters.
    Verifies pagination count and results length.
    """
    # Create multiple expenses using the factory
    expense1 = ExpenseFactory()
    expense2 = ExpenseFactory()
    expense3 = ExpenseFactory()

    url = reverse("api:list_expenses")
    response = api_client.get(url)

    assert response.status_code == 200
    data = json.loads(response.content)["results"]
    print(f"total count: {json.loads(response.content)['total']}")

    assert isinstance(data, list)
    assert len(data) == 3  # We created 3 expenses

    found_uuids = {item["uuid"] for item in data}
    assert str(expense1.uuid) in found_uuids
    assert str(expense2.uuid) in found_uuids
    assert str(expense3.uuid) in found_uuids


@pytest.mark.django_db
def test_list_expenses_filter_status(api_client):
    """
    Tests filtering expenses by approval status.
    """
    ExpenseFactory(status=ApprovalStatus.PENDING.value)
    ExpenseFactory(status=ApprovalStatus.APPROVED.value)
    ExpenseFactory(status=ApprovalStatus.PENDING.value)
    ExpenseFactory(status=ApprovalStatus.DECLINED.value)

    url = reverse("api:list_expenses") + f"?status={ApprovalStatus.PENDING.value}"
    response = api_client.get(url)
    assert response.status_code == 200
    data = json.loads(response.content)["results"]

    assert isinstance(data, list)
    assert len(data) == 2
    for expense_data in data:
        assert expense_data["status"] == ApprovalStatus.PENDING.value


@pytest.mark.django_db
def test_list_expenses_filter_employee_uuid(api_client):
    """
    Tests filtering expenses by employee UUID.
    """
    employee_id_1 = UUID("a0a0a0a0-a0a0-40a0-80a0-a0a0a0a0a0a0")
    employee_id_2 = UUID("b1b1b1b1-b1b1-41b1-81b1-b1b1b1b1b1b1")

    ExpenseFactory(uuid=employee_id_1)
    ExpenseFactory(uuid=employee_id_2)

    url = reverse("api:list_expenses") + f"?employee_uuid={employee_id_1}"
    response = api_client.get(url)

    assert response.status_code == 200
    data = json.loads(response.content)["results"]

    assert isinstance(data, list)
    assert len(data) == 1
    for expense_data in data:
        assert expense_data["uuid"] == str(employee_id_1)


@pytest.mark.django_db
def test_list_expenses_filter_amount_range(api_client):
    """
    Tests filtering expenses by amount range.
    """
    ExpenseFactory(amount=50.0)
    ExpenseFactory(amount=150.0)
    ExpenseFactory(amount=250.0)
    ExpenseFactory(amount=300.0)

    url = reverse("api:list_expenses") + "?min_amount=100&max_amount=200"
    response = api_client.get(url)

    assert response.status_code == 200
    data = json.loads(response.content)["results"]

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["amount"] == 150.0


@pytest.mark.django_db
def test_list_expenses_filter_currency(api_client):
    """
    Tests filtering expenses by currency.
    """
    ExpenseFactory(currency="USD")
    ExpenseFactory(currency="EUR")
    ExpenseFactory(currency="USD")

    url = reverse("api:list_expenses") + "?currency=usd"
    response = api_client.get(url)

    assert response.status_code == 200
    data = json.loads(response.content)["results"]

    assert isinstance(data, list)
    assert len(data) == 2
    for expense_data in data:
        assert expense_data["currency"] == "USD"


@pytest.mark.django_db
def test_list_expenses_search_description(api_client):
    """
    Tests searching expenses by description.
    """
    ExpenseFactory(description="Travel expenses for London trip")
    ExpenseFactory(description="Office supplies purchase")
    ExpenseFactory(description="Dinner in london with client")

    url = reverse("api:list_expenses") + "?search_description=london"
    response = api_client.get(url)

    assert response.status_code == 200
    data = json.loads(response.content)["results"]

    assert isinstance(data, list)
    assert len(data) == 2
    assert "london" in data[0]["description"].lower()
    assert "london" in data[1]["description"].lower()


@pytest.mark.django_db
def test_get_expense_success(api_client):
    """
    Tests retrieving a single expense successfully.
    """
    expense = ExpenseFactory()
    url = reverse("api:get_expense", kwargs={"expense_uuid": expense.uuid})
    response = api_client.get(url)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["uuid"] == str(expense.uuid)
    assert data["description"] == expense.description
    assert data["amount"] == expense.amount
    assert data["currency"] == expense.currency
    assert data["status"] == expense.status


@pytest.mark.django_db
def test_get_expense_not_found(api_client):
    """
    Tests retrieving a non-existent expense returns 404.
    """
    non_existent_uuid = UUID("c2c2c2c2-c2c2-42c2-82c2-c2c2c2c2c2c2")
    url = reverse("api:get_expense", kwargs={"expense_uuid": non_existent_uuid})
    response = api_client.get(url)
    assert response.status_code == 404
    assert (
        json.loads(response.content)
        == ExpenseNotFound(str(non_existent_uuid)).to_schema().model_dump()
    )


@pytest.mark.django_db
def test_update_expense_status_success_approved(api_client):
    """
    Tests successfully updating a pending expense to APPROVED.
    """
    expense = ExpenseFactory(status=ApprovalStatus.PENDING.value)
    url = reverse("api:update_expense_status", kwargs={"expense_uuid": expense.uuid})
    payload = {"status": ApprovalStatus.APPROVED.value}
    response = api_client.put(url, json.dumps(payload), content_type="application/json")

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["uuid"] == str(expense.uuid)
    assert data["status"] == ApprovalStatus.APPROVED.value

    expense.refresh_from_db()
    assert expense.status == ApprovalStatus.APPROVED.value


@pytest.mark.django_db
def test_update_expense_status_success_declined(api_client):
    """
    Tests successfully updating a pending expense to DECLINED.
    """
    expense = ExpenseFactory(status=ApprovalStatus.PENDING.value)
    url = reverse("api:update_expense_status", kwargs={"expense_uuid": expense.uuid})
    payload = {"status": ApprovalStatus.DECLINED.value}
    response = api_client.put(url, json.dumps(payload), content_type="application/json")

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["uuid"] == str(expense.uuid)
    assert data["status"] == ApprovalStatus.DECLINED.value

    expense.refresh_from_db()
    assert expense.status == ApprovalStatus.DECLINED.value


@pytest.mark.django_db
def test_update_expense_status_not_found(api_client):
    """
    Tests updating a non-existent expense returns 404.
    """
    non_existent_uuid = UUID("d3d3d3d3-d3d3-43d3-83d3-d3d3d3d3d3d3")
    url = reverse(
        "api:update_expense_status", kwargs={"expense_uuid": non_existent_uuid}
    )
    payload = {"status": ApprovalStatus.APPROVED.value}
    response = api_client.put(url, json.dumps(payload), content_type="application/json")
    assert response.status_code == 404
    assert (
        json.loads(response.content)
        == ExpenseNotFound(str(non_existent_uuid)).to_schema().model_dump()
    )


@pytest.mark.django_db
def test_update_expense_status_invalid_payload(api_client):
    """
    Tests updating an expense with an invalid status value in the payload.
    """
    expense = ExpenseFactory(status=ApprovalStatus.PENDING.value)
    url = reverse("api:update_expense_status", kwargs={"expense_uuid": expense.uuid})
    payload = {"status": "INVALID_STATUS"}
    response = api_client.put(url, json.dumps(payload), content_type="application/json")
    assert response.status_code == 400
    assert (
        json.loads(response.content)
        == InvalidStatusError(status="INVALID_STATUS").to_schema().model_dump()
    )


@pytest.mark.django_db
def test_update_expense_status_already_approved(api_client):
    """
    Tests attempting to update an already APPROVED expense.
    Should return 409 Conflict based on service layer logic.
    """
    expense = ExpenseFactory(status=ApprovalStatus.APPROVED.value)
    url = reverse("api:update_expense_status", kwargs={"expense_uuid": expense.uuid})
    payload = {"status": ApprovalStatus.DECLINED.value}
    response = api_client.put(url, json.dumps(payload), content_type="application/json")

    assert response.status_code == 409
    assert (
        json.loads(response.content)
        == ExpenseAlreadyProcessedError(str(expense.uuid)).to_schema().model_dump()
    )

    expense.refresh_from_db()
    assert expense.status == ApprovalStatus.APPROVED.value


@pytest.mark.django_db
def test_update_expense_status_already_declined(api_client):
    """
    Tests attempting to update an already DECLINED expense.
    Should return 409 Conflict based on service layer logic.
    """
    expense = ExpenseFactory(status=ApprovalStatus.DECLINED.value)
    url = reverse("api:update_expense_status", kwargs={"expense_uuid": expense.uuid})
    payload = {"status": ApprovalStatus.APPROVED.value}
    response = api_client.put(url, json.dumps(payload), content_type="application/json")

    assert response.status_code == 409
    assert (
        json.loads(response.content)
        == ExpenseAlreadyProcessedError(str(expense.uuid)).to_schema().model_dump()
    )

    expense.refresh_from_db()
    assert expense.status == ApprovalStatus.DECLINED.value
