# RepairTrack

Django student project: Electronics Service & Repair Tracking Portal.

Setup:
1. python -m venv venv
2. Activate the environment
3. pip install -r requirements.txt
4. python manage.py makemigrations
5. python manage.py migrate
6. python manage.py createsuperuser
7. python manage.py runserver

URLs:
Home: /
Common login: /login/
Customer registration: /customer/register/
Customer dashboard: /customer/dashboard/
Technician dashboard: /technician/dashboard/
Custom admin dashboard: /admin-dashboard/
Django admin: /django-admin/

Login routing: customer -> customer dashboard; technician -> technician dashboard; staff/superuser -> admin dashboard.
