from django.contrib import admin
from .models import Employee, Expense


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("uuid", "first_name", "last_name")
    search_fields = ("first_name", "last_name", "uuid")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "description",
        "amount",
        "currency",
        "employee",
        "status",
        "created_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = (
        "description",
        "uuid",
        "employee__first_name",
        "employee__last_name",
    )
    raw_id_fields = ("employee",)  # Better for selecting employees if many
    readonly_fields = ("uuid", "created_at")  # These fields are set on creation
