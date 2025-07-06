import factory
import factory.fuzzy
import datetime
import uuid

from django.utils import timezone

# Import models from the same app
from expense_manager.models import Expense, Employee, ApprovalStatus


class EmployeeFactory(factory.django.DjangoModelFactory):
    """
    Factory for generating Employee model instances.
    """

    class Meta:
        model = Employee

    uuid = factory.LazyFunction(uuid.uuid4)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class ExpenseFactory(factory.django.DjangoModelFactory):
    """
    Factory for generating Expense model instances.
    Uses Faker for realistic data generation and integrates EmployeeFactory.
    """

    class Meta:
        model = Expense

    uuid = factory.LazyFunction(uuid.uuid4)
    description = factory.Faker("sentence", nb_words=10)
    amount = factory.fuzzy.FuzzyFloat(1.0, 1000.0, precision=2)
    currency = factory.fuzzy.FuzzyChoice(["USD", "EUR", "GBP", "JPY", "CAD"])
    created_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - datetime.timedelta(days=365), end_dt=timezone.now()
    )

    employee = factory.SubFactory(EmployeeFactory)
    status = ApprovalStatus.PENDING.value

    @classmethod
    def _after_postgeneration(cls, obj, create, results=None):
        """
        Post-generation hook to set employee_uuid, first_name, and last_name
        directly on the Expense object from the associated Employee object.
        This runs after the Expense object and its related Employee object are created.
        """
        if create:
            obj.employee_uuid = obj.employee.uuid
            obj.employee_first_name = obj.employee.first_name
            obj.employee_last_name = obj.employee.last_name
            obj.save()
