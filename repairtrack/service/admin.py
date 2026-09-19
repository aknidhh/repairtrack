from django.contrib import admin
from .models import UserProfile,Device,ServiceTicket,Repair,SparePart,WarrantyClaim,Notification,AuditLog
admin.site.register([UserProfile,Device,ServiceTicket,Repair,SparePart,WarrantyClaim,Notification,AuditLog])
