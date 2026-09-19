from functools import wraps
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from django.shortcuts import render,redirect,get_object_or_404
from .models import UserProfile,Device,ServiceTicket,Repair,SparePart,WarrantyClaim,Notification,AuditLog

# home page
def home(request):
  return render(request,"home.html")

def go(user):
 if user.is_staff or user.is_superuser:return redirect("admin_dashboard")
 try:r=user.profile.role
 except UserProfile.DoesNotExist:r="customer"
 return redirect({"technician":"technician_dashboard","admin":"admin_dashboard"}.get(r,"customer_dashboard"))

def login_view(request):
 if request.user.is_authenticated:return go(request.user)
 if request.method=="POST":
  u=authenticate(request,username=request.POST.get("username",""),
                 password=request.POST.get("password",""))
  if u: login(request,u); return go(u)
  messages.error(request,"Invalid username or password.")
 return render(request,"login.html")

def logout_view(request): 
    logout(request)
    return redirect("home")

def customer_register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        pw = request.POST.get("password", "")
        cpw = request.POST.get("confirm_password", "")
        email = request.POST.get("email", "").strip()
        if pw != cpw:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(
                username=username,
                password=pw,
                email=email
            )
            messages.success(request, "Registration successful.")
            return redirect("login")
    return render(request, "customer_register.html")

def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        @login_required
        def wrap(request,*a,**kw):
            if request.user.is_staff or request.user.is_superuser:
                if "admin" in roles:return fn(request,*a,**kw)
            try:r=request.user.profile.role
            except UserProfile.DoesNotExist:r="customer"
            return fn(request,*a,**kw) if r in roles else go(request.user)
        return wrap
    return deco

@role_required("customer")
def customer_dashboard(request):
    t=ServiceTicket.objects.filter(customer=request.user).select_related("device","technician")
    return render(request,"customer_dashboard.html",
                  {"device_count":Device.objects.filter(customer=request.user).count(),
                   "open_count":t.exclude(status__in=["completed","cancelled"]).count(),
                   "active_count":t.filter(status__in=["diagnosing","repairing"]).count(),
                   "completed_count":t.filter(status="completed").count(),"recent_tickets":t[:8]})

@role_required("technician")
def technician_dashboard(request):
    t=ServiceTicket.objects.filter(technician=request.user).select_related("customer","device")
    return render(request,"technician_dashboard.html",{"assigned_count":t.count(),
                                                       "active_count":t.filter(status__in=["diagnosing","repairing"]).count(),
                                                       "diagnosis_count":t.filter(status="diagnosing").count(),
                                                       "completed_count":t.filter(status="completed").count(),"assigned_tickets":t[:10]})

@role_required("admin")
def admin_dashboard(request):
  t=ServiceTicket.objects.all()
  return render(request,"admin_dashboard.html",{"customer_count":UserProfile.objects.filter(role="customer").count(),
                                               "technician_count":UserProfile.objects.filter(role="technician").count(),
                                               "ticket_count":t.count(),"open_ticket_count":t.exclude(status__in=["completed","cancelled"]).count(),
                                               "repairing_count":t.filter(status="repairing").count(),"low_stock_count":sum(p.low_stock for p in SparePart.objects.all()),
                                               "recent_tickets":t[:8]})

@role_required("admin")
def add_technician(request):
 if request.method=="POST":
  un=request.POST.get("username","").strip()
  if User.objects.filter(username=un).exists():messages.error(request,"Username already exists.")
  else:
   u=User.objects.create_user(username=un,password=request.POST.get("password",""),
                              email=request.POST.get("email",""),
                              first_name=request.POST.get("first_name",""),
                              last_name=request.POST.get("last_name",""))
   UserProfile.objects.create(user=u,role="technician",phone=request.POST.get("phone",""))
   AuditLog.objects.create(actor=request.user,action=f"Added technician {un}")
   messages.success(request,"Technician created."); return redirect("admin_users")
 return render(request,"add_technician.html")

@role_required("admin")
def admin_users(request):
  return render(request,"admin_users.html",
                {"profiles":UserProfile.objects.select_related("user").all()})
@role_required("admin")
def audit_logs(request):
  return render(request,"audit_logs.html",
                {"logs":AuditLog.objects.select_related("actor")[:100]})

@role_required("admin")
def assign_technician(request, ticket_id):
    ticket = get_object_or_404(
        ServiceTicket,
        pk=ticket_id)
    technicians = User.objects.filter(
        profile__role="technician",
        is_active=True).order_by("first_name", "username")
    if request.method == "POST":
        technician_id = request.POST.get("technician")
        if not technician_id:
            messages.error(
                request,
                "Please select a technician.")
            return redirect(
                "assign_technician",
                ticket_id=ticket.id)
        technician = get_object_or_404(
            User,
            id=technician_id,
            profile__role="technician")
        ticket.technician = technician 
        if ticket.status == "submitted":
            ticket.status = "diagnosing"
        ticket.save()
        AuditLog.objects.create(
            actor=request.user,
            action=(
                f"Assigned technician "
                f"{technician.username} "
                f"to ticket RT-{ticket.id:04d}"))
        Notification.objects.create(
            recipient=ticket.customer,
            title="Technician assigned",
            message=(
                f"Technician has been assigned to "
                f"your repair ticket RT-{ticket.id:04d}." ))
        messages.success(
            request,
            f"{technician.get_full_name() or technician.username} "
            f"assigned successfully.")
        return redirect("tickets")
    return render(
        request,
        "assign_technician.html",
        {
            "ticket": ticket,
            "technicians": technicians
        }
    )

@login_required
def devices(request):
 ds=Device.objects.all() if request.user.is_staff else Device.objects.filter(customer=request.user)
 return render(request,"devices.html",{"devices":ds})

@role_required("customer")
def register_device(request):
 if request.method=="POST":
  Device.objects.create(customer=request.user,name=request.POST.get("name",""),
                        brand=request.POST.get("brand",""),
                        model_number=request.POST.get("model_number",""),
                        serial_number=request.POST.get("serial_number",""))
  return redirect("devices")
 return render(request,"register_device.html")

@login_required
def tickets(request):
 try:r=request.user.profile.role
 except UserProfile.DoesNotExist:r="customer"
 if request.user.is_staff:t=ServiceTicket.objects.all()
 elif r=="technician":t=ServiceTicket.objects.filter(technician=request.user)
 else:t=ServiceTicket.objects.filter(customer=request.user)
 return render(request,"tickets.html",{"tickets":t.select_related("customer","device","technician")})

@role_required("customer")
def create_ticket(request):
 ds=Device.objects.filter(customer=request.user)
 if request.method=="POST":
  d=get_object_or_404(ds,pk=request.POST.get("device"))
  t=ServiceTicket.objects.create(customer=request.user,device=d,title=request.POST.get("title",""),
                                 description=request.POST.get("description",""),
                                 priority=request.POST.get("priority","normal"))
  Repair.objects.create(ticket=t)
  return redirect("tickets")
 return render(request,"create_ticket.html",{"devices":ds})

@role_required("technician","admin")
def update_ticket_status(request,ticket_id):
 t=get_object_or_404(ServiceTicket,pk=ticket_id)
 if request.method=="POST" and request.POST.get("status") in dict(ServiceTicket.STATUS):
  t.status=request.POST["status"]; t.save(); Notification.objects.create(recipient=t.customer,title="Repair status updated",
                                                                         message=f"RT-{t.pk:04d} is now {t.get_status_display()}.")
 return redirect("tickets")

@login_required
def repairs(request):
 try:r=request.user.profile.role
 except UserProfile.DoesNotExist:r="customer"
 q=Repair.objects.select_related("ticket","ticket__customer","ticket__device")
 if request.user.is_staff:
    q=q.all()
 elif r=="technician":
    q=q.filter(ticket__technician=request.user)
 else:
    q=q.filter(ticket__customer=request.user)
 return render(request,"repairs.html",{"repairs":q})

@role_required("technician", "admin")
def inventory(request):
    parts = SparePart.objects.all().order_by("name")
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        part_number = request.POST.get("part_number", "").strip()
        quantity = request.POST.get("quantity", "0")
        minimum_quantity = request.POST.get("minimum_quantity", "1")
        unit_price = request.POST.get("unit_price", "0")
        if not name or not part_number:
            messages.error(request,"Part name and part number are required.")
            return redirect("inventory")
        if SparePart.objects.filter(part_number=part_number).exists():
            messages.error(request,"This part number already exists.")
            return redirect("inventory")
        try:
            quantity = int(quantity)
            minimum_quantity = int(minimum_quantity)
            unit_price = float(unit_price)
            if quantity < 0:
                raise ValueError
            if minimum_quantity < 0:
                raise ValueError
            if unit_price < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request,"Please enter valid stock and price values.")
            return redirect("inventory")
        part = SparePart.objects.create(
            name=name,
            part_number=part_number,
            quantity=quantity,
            minimum_quantity=minimum_quantity,
            unit_price=unit_price)
        AuditLog.objects.create(actor=request.user,action=(f"Added inventory part "f"{part.name} ({part.part_number})"))
        messages.success(request,f"{part.name} added to inventory successfully.")
        return redirect("inventory")
    return render( request, "inventory.html",{ "parts": parts})

@role_required("admin")
def admin_warranty_claims(request):
    claims = WarrantyClaim.objects.filter(
        status="submitted").select_related("customer","device")
    return render(request, "admin_warranty_claims.html",{ "claims": claims})

@role_required("admin")
def review_warranty_claim(request, claim_id):
    claim = get_object_or_404(WarrantyClaim,id=claim_id)
    if request.method == "POST":
        action = request.POST.get("action")
        admin_note = request.POST.get("admin_note","").strip()
        if action == "approve":
            claim.status = "approved"
            Notification.objects.create(
                recipient=claim.customer,
                title="Warranty Claim Approved",
                message=(f"Your warranty claim for "f"{claim.device} has been approved."))
            AuditLog.objects.create(
                actor=request.user,
                action=(f"Approved warranty claim "f"#{claim.id}"))
            messages.success(request,"Warranty claim approved.")
        elif action == "reject":
            claim.status = "rejected"
            Notification.objects.create(
                recipient=claim.customer,
                title="Warranty Claim Rejected",
                message=(f"Your warranty claim for "f"{claim.device} has been rejected."))
            AuditLog.objects.create(
                actor=request.user,
                action=(f"Rejected warranty claim "f"#{claim.id}"))
            messages.warning(request,"Warranty claim rejected.")
        else:
            messages.error(request,"Invalid action.")
            return redirect("review_warranty_claim",claim_id=claim.id)
        claim.admin_note = admin_note
        claim.reviewed_at = timezone.now()
        claim.save()
        return redirect("admin_warranty_claims")
    return render(request,"review_warranty_claim.html",{"claim": claim})

@role_required("customer")
def warranty(request):
    devices = Device.objects.filter(
        customer=request.user)
    claims = WarrantyClaim.objects.filter(customer=request.user).select_related("device")
    if request.method == "POST":
        device_id = request.POST.get("device")
        description = request.POST.get("description", "").strip()
        if not device_id:
            messages.error(
                request,
                "Please select a device.")
            return redirect("warranty")
        if not description:
            messages.error(
                request,
                "Please describe the warranty problem.")
            return redirect("warranty")
        device = get_object_or_404(
            Device,
            id=device_id,
            customer=request.user)
        WarrantyClaim.objects.create(
            customer=request.user,
            device=device,
            description=description,
            status="submitted")
        admins = User.objects.filter(
            is_staff=True,
            is_active=True)
        for admin_user in admins:
            Notification.objects.create(
                recipient=admin_user,
                title="New Warranty Claim",
                message=(
                    f"{request.user.username} submitted "
                    f"a warranty claim for {device}."))
        AuditLog.objects.create(
            actor=request.user,
            action=(f"Submitted warranty claim "f"for {device}"))
        messages.success(request,"Warranty claim submitted successfully.")
        return redirect("warranty")
    return render(request,"warranty.html",{"claims": claims,"devices": devices})

@login_required
def notifications(request):
  return render(request,"notifications.html",
                {"notifications":Notification.objects.filter(recipient=request.user)})

@role_required("admin")
def reports(request):
  return render(request,"reports.html",
                {"status_data":ServiceTicket.objects.values("status").annotate(total=Count("id"))})

@login_required
def profile(request):
 p,_=UserProfile.objects.get_or_create(user=request.user)
 if request.method=="POST":
  request.user.first_name=request.POST.get("first_name","")
  request.user.last_name=request.POST.get("last_name","")
  request.user.email=request.POST.get("email","")
  request.user.save(); p.phone=request.POST.get("phone","")
  p.save(); return redirect("profile")
 return render(request,"profile.html",{"profile":p})