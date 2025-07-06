from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from expense_manager.api import router
from django.conf import settings

api = NinjaAPI(title="Cashcog Expense API", urls_namespace="api")

api.add_router("/expenses/", router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

if settings.DEBUG:
    from django.conf import settings
    from django.conf.urls.static import static

    # Serve static files in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # type: ignore
