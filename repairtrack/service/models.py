from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES=(("customer","Customer"),
                  ("technician","Technician"),
                  ("admin","Admin"))
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default="customer")
    phone=models.CharField(max_length=20,blank=True)
    def __str__(self): 
       return f"{self.user.username} - {self.role}"

class Device(models.Model):
    customer=models.ForeignKey(User,on_delete=models.CASCADE,related_name="devices")
    name=models.CharField(max_length=120); brand=models.CharField(max_length=80,blank=True)
    model_number=models.CharField(max_length=80,blank=True); serial_number=models.CharField(max_length=120,blank=True)
    registered_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):
       return f"{self.brand} {self.name}".strip()

class ServiceTicket(models.Model):
    STATUS=(("submitted","Submitted"),
            ("diagnosing","Diagnosing"),
            ("repairing","Repairing"),
            ("ready","Ready for Collection"),
            ("completed","Completed"),
            ("cancelled","Cancelled"))
    PRIORITY=(("normal","Normal"),
              ("medium","Medium"),
              ("high","High"))
    customer=models.ForeignKey(User,on_delete=models.CASCADE,related_name="tickets")
    device=models.ForeignKey(Device,on_delete=models.CASCADE,related_name="tickets")
    technician=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="assigned_tickets")
    title=models.CharField(max_length=160); description=models.TextField()
    priority=models.CharField(max_length=20,choices=PRIORITY,default="normal")
    status=models.CharField(max_length=20,choices=STATUS,default="submitted")
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    def __str__(self): 
       return f"RT-{self.pk:04d} - {self.title}"

class Repair(models.Model):
    ticket=models.OneToOneField(ServiceTicket,on_delete=models.CASCADE,related_name="repair")
    diagnosis=models.TextField(blank=True); work_notes=models.TextField(blank=True)
    estimated_cost=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    started_at=models.DateTimeField(null=True,blank=True); completed_at=models.DateTimeField(null=True,blank=True)

class SparePart(models.Model):
    name=models.CharField(max_length=120); part_number=models.CharField(max_length=80,unique=True)
    quantity=models.PositiveIntegerField(default=0); minimum_quantity=models.PositiveIntegerField(default=1)
    unit_price=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    @property
    def low_stock(self):
        return self.quantity<=self.minimum_quantity

class WarrantyClaim(models.Model):
    STATUS_CHOICES = (("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),)
    customer = models.ForeignKey(User,on_delete=models.CASCADE,related_name="warranty_claims")
    device = models.ForeignKey(Device,on_delete=models.CASCADE,related_name="warranty_claims")
    description = models.TextField()
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="submitted")
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True,blank=True)
    def __str__(self):
        return f"Warranty Claim #{self.id} - {self.device}"

class Notification(models.Model):
    recipient=models.ForeignKey(User,on_delete=models.CASCADE,related_name="notifications")
    title=models.CharField(max_length=160); message=models.TextField()
    is_read=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    actor=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    action=models.CharField(max_length=250); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-created_at"]
