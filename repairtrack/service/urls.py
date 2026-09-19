from django.urls import path
from . import views

urlpatterns=[
    
path("", views.home, name="home"),
path("login/", views.login_view, name="login"),    
path("customer/register/", views.customer_register,name="customer_register"),
path("logout/", views.logout_view, name="logout"),
path("customer/dashboard/",views.customer_dashboard,name="customer_dashboard"),
path("technician/dashboard/",views.technician_dashboard,name="technician_dashboard"),
path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
path("admin/technicians/add/",views.add_technician,name="add_technician"),
path("admin/users/",views.admin_users,name="admin_users"),
path("admin/audit-logs/",views.audit_logs,name="audit_logs"),
path("devices/",views.devices,name="devices"),
path("devices/register/",views.register_device,name="register_device"),
path("tickets/",views.tickets,name="tickets"),
path("tickets/create/",views.create_ticket,name="create_ticket"),
path("tickets/<int:ticket_id>/assign/",views.assign_technician,name="assign_technician"),
path("tickets/<int:ticket_id>/status/",views.update_ticket_status,name="update_ticket_status"),
path("repairs/",views.repairs,name="repairs"),
path("inventory/",views.inventory,name="inventory"),
path("admin/warranty/",views.admin_warranty_claims,name="admin_warranty_claims"),
path("admin/warranty/<int:claim_id>/review/",views.review_warranty_claim,name="review_warranty_claim"),
path("warranty/",views.warranty,name="warranty"),
path("notifications/",views.notifications,name="notifications"),
path("reports/",views.reports,name="reports"),path("profile/",views.profile,name="profile")

]