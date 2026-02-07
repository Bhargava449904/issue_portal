from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User
import bcrypt
import jwt
import datetime
from django.conf import settings
from .utils import get_user_from_token
SECRET_KEY=settings.SECRET_KEY

def welcome(request):
    return HttpResponse("hello")

# # ---------------- REGISTER API (Citizen Only) ----------------
@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    username = request.POST.get("username")
    email = request.POST.get("email")
    password = request.POST.get("password")
    password=password.encode("utf-8")
    salt=bcrypt.gensalt(rounds=13)
    encrypted_password=bcrypt.hashpw(password=password,salt=salt)
    encrypted_password=encrypted_password.decode("utf-8")

    if not username or not email or not password:
        return JsonResponse({"error": "All fields are required"}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email already registered"}, status=400)

    User.objects.create(
        username=username,
        email=email,
        password=encrypted_password,
        role="citizen"   # 🔒 citizen only
    )

    return JsonResponse({
        "message": "Registration successful",
        "role": "citizen"
    }, status=201)


# # ---------------- LOGIN API (Citizen + Admin) ----------------
@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    email = request.POST.get("email")
    password = request.POST.get("password")
    if not email or not password:
        return JsonResponse({"error": "Email and password required"}, status=400) 
    try:
        database_data=User.objects.get(email=email)
        database_data_hashpassword=database_data.password
        issame=bcrypt.checkpw(password.encode("utf-8"),database_data_hashpassword.encode("utf-8"))
        if issame:
            payload = {
            "user_id": database_data.id,
            "role": database_data.role,
            "is_super_admin": database_data.is_super_admin,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            response = JsonResponse({
                "message": "Login successful",
                "role": database_data.role
            })

            response.set_cookie(
                key="token",
                value=token,
                httponly=True,
                secure=True,
                samesite="none"
            )
            return response
        else:
            return JsonResponse("invalid credentials")
    except:
        return JsonResponse("user not available")
    
    


# # # ---------------- LOGOUT API ----------------
# # @csrf_exempt
# # def logout_api(request):
# #     response = JsonResponse({"message": "Logout successful"})
# #     response.delete_cookie("token")
# #     return response

@csrf_exempt
def super_admin_create_admin(request):
    #  Allow only POST
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    # Authenticate user
    user = get_user_from_token(request)
    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # SUPER ADMIN check (IMPORTANT)
    if not user or (
    user.get("role") != "admin"
    or not user.get("is_super_admin")
    ):
        return JsonResponse({"error": "Super Admin only"}, status=403)

    #  Get data
    username = request.POST.get("username")
    email = request.POST.get("email")
    password = request.POST.get("password")

    if not username or not email or not password:
        return JsonResponse({"error": "All fields are required"}, status=400)

    # Check existing email
    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email already exists"}, status=400)

    # Hash password
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # Create NORMAL admin
    User.objects.create(
        username=username,
        email=email,
        password=hashed_password,
        role="admin",
        is_super_admin=False   # ⭐ normal admin
    )

    # Success response
    return JsonResponse(
        {"message": "Normal admin created successfully"},
        status=201
    )



@csrf_exempt
def super_admin_view_admins(request):
    # Allow only GET
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    # Authenticate user
    user = get_user_from_token(request)
    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Super admin check
    if not user or (
    user.get("role") != "admin"
    or not user.get("is_super_admin")
    ):
        return JsonResponse({"error": "Super Admin only"}, status=403)

    # Fetch ONLY normal admins
    admins = User.objects.filter(
        role="admin",
        is_super_admin=False
    ).order_by("id")

    data = []
    for admin in admins:
        data.append({
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "created_at": admin.created_at
        })

    return JsonResponse({"admins": data}, status=200)


@csrf_exempt
def super_admin_delete_admin(request, admin_id):
    # Allow only DELETE
    if request.method != "DELETE":
        return JsonResponse({"error": "DELETE method required"}, status=405)

    # Authenticate user
    user = get_user_from_token(request)
    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Super admin check
    if not user or (
    user.get("role") != "admin"
    or not user.get("is_super_admin")
    ):
        return JsonResponse({"error": "Super Admin only"}, status=403)

    # Prevent self delete
    if user["user_id"] == admin_id:
        return JsonResponse(
            {"error": "Super admin cannot delete himself"},
            status=400
        )

    # Fetch target admin
    try:
        target_admin = User.objects.get(id=admin_id, role="admin")
    except User.DoesNotExist:
        return JsonResponse({"error": "Admin not found"}, status=404)

    # Protect super admin
    if target_admin.is_super_admin:
        return JsonResponse(
            {"error": "Super admin cannot be deleted"},
            status=403
        )

    # Delete normal admin
    target_admin.delete()

    return JsonResponse(
        {"message": "Normal admin deleted successfully"},
        status=200
    )

