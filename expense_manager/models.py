import uuid
from django.db import models
import enum


class ApprovalStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.title()) for key in cls]


class Employee(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # type: ignore
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    last_name = models.CharField(max_length=100, verbose_name="Last Name")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.uuid})"

    class Meta:
        verbose_name_plural = "Employees"
        ordering = ["last_name", "first_name"]  # Add default ordering


class Expense(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # type: ignore
    description = models.TextField(verbose_name="Description")
    created_at = models.DateTimeField(verbose_name="Created At")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount")
    currency = models.CharField(max_length=10, verbose_name="Currency")
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name="Employee",
    )
    status = models.CharField(
        max_length=10,
        choices=ApprovalStatus.choices(),
        default=ApprovalStatus.PENDING.value,
        verbose_name="Approval Status",
    )

    def __str__(self):
        return f"Expense {self.uuid} - {self.description[:30]}..."

    class Meta:
        verbose_name_plural = "Expenses"
        ordering = ["-created_at"]
