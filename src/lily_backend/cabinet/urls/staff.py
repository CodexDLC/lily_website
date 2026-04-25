from django.urls import path

from ..views.services import CategoryStatusToggleView, ServiceQuickEditView, ServicesListView
from ..views.staff import StaffListView, StaffQuickEditView
from ..views.users import ClientDetailView, UserListView

staff_urlpatterns = [
    # Users / Clients
    path("users/", UserListView.as_view(), name="users_list"),
    path("users/modal/<str:id_token>/", ClientDetailView.as_view(), name="user_modal"),
    path("users/<str:id_token>/modal/", ClientDetailView.as_view(), name="user_modal_legacy"),
    path("clients/ghost/<int:pk>/modal/", ClientDetailView.as_view(), name="client_ghost_modal"),
    # Staff / Masters
    path("staff/", StaffListView.as_view(), name="staff_list"),
    path("staff/modal/<int:pk>/", StaffQuickEditView.as_view(), name="staff_modal"),
    # Services catalog management
    path("services/", ServicesListView.as_view(), name="services_list"),
    path("services/<slug:category_slug>/", ServicesListView.as_view(), name="services_category"),
    path("services/<int:pk>/quick-edit/", ServiceQuickEditView.as_view(), name="service_quick_edit"),
    path("services/category/<int:pk>/toggle/", CategoryStatusToggleView.as_view(), name="service_category_toggle"),
    path("services/g/<str:group>/", ServicesListView.as_view(), name="services_group"),
]
