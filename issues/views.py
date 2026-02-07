from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from acoounts.utils import get_user_from_token
from issues.models import Issue
import cloudinary
import cloudinary.uploader
import bcrypt
from acoounts.models import User
import json
# Create your views here.

def hello(request):
    return HttpResponse("hello")


@csrf_exempt
def create_issue(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    
    user = get_user_from_token(request)
    print("USER FROM TOKEN:", user)
    if not user or user["role"] != "citizen":
        return JsonResponse({"error": "Citizen only"}, status=403)
    
    title = request.POST.get("title")
    description = request.POST.get("description")
    location = request.POST.get("location")
    image = request.FILES.get("image")
    image_url = cloudinary.uploader.upload(image)

    if not title or not description:
        return JsonResponse(
            {"error": "Title and description are required"},
            status=400
        )
    
    Issue.objects.create(
        title=title,
        description=description,
        image=image_url["secure_url"],  
        location=location,                    
        created_by_id=user["user_id"]     # user id from token
    )

    return JsonResponse(
        {"message": "Issue created successfully"},
        status=201
    )


# citizen will see only his issue

@csrf_exempt
def view_my_issues(request):
    #  Allow only GET
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    # Authenticate user
    user = get_user_from_token(request)
    if not user or user["role"] != "citizen":
        return JsonResponse({"error": "Citizen only"}, status=403)

    #  Fetch only logged-in citizen issues
    issues = Issue.objects.filter(created_by_id=user["user_id"]).order_by("-created_at")

    #  Convert queryset to JSON
    issues_data = []
    for issue in issues:
        issues_data.append({
            "id": issue.id,
            "title": issue.title,
            "description": issue.description,
            "location": issue.location,
            "status": issue.status,
            "image": issue.image,   # Cloudinary URL
            "created_at": issue.created_at
        })

    #  Return response
    return JsonResponse(
        {"issues": issues_data},
        status=200
    )
    


# here admin will see all the issues rasied by citizen


@csrf_exempt
def admin_view_all_issues(request):
    # Allow only GET
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    #  Authenticate user
    user = get_user_from_token(request)
    if not user or user["role"] != "admin":
        return JsonResponse({"error": "Admin only"}, status=403)

    #  Fetch all issues
    issues = Issue.objects.select_related("created_by").order_by("-created_at")

    # Convert queryset to JSON
    issues_data = []
    for issue in issues:
        issues_data.append({
            "id": issue.id,
            "title": issue.title,
            "description": issue.description,
            "location": issue.location,
            "status": issue.status,
            "image": issue.image,  # Cloudinary URL
            "created_at": issue.created_at,

            # Citizen details
            "reported_by": {
                "user_id": issue.created_by.id,
                "username": issue.created_by.username,
                "email": issue.created_by.email,
            }
        })

    # Return response
    return JsonResponse(
        {"issues": issues_data},
        status=200
    )



# admin update status of the issue

@csrf_exempt
def admin_update_issue_status(request, issue_id):

    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    # authenticate admin
    user = get_user_from_token(request)
    if not user or user["role"] != "admin":
        return JsonResponse({"error": "Admin only"}, status=403)

    try:
        body = json.loads(request.body)
        new_status = body.get("status")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    allowed_status = ["pending", "in_progress", "resolved"]
    if new_status not in allowed_status:
        return JsonResponse({"error": "Invalid status"}, status=400)

    try:
        issue = Issue.objects.get(id=issue_id)
    except Issue.DoesNotExist:
        return JsonResponse({"error": "Issue not found"}, status=404)

    issue.status = new_status
    issue.save()

    return JsonResponse({
        "message": "Status updated successfully",
        "issue_id": issue.id,
        "status": issue.status
    }, status=200)



@csrf_exempt
def user_get_issues(request):

    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    user = get_user_from_token(request)
    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    issues = Issue.objects.filter(user_id=user["id"]).order_by("-id")

    data = []
    for issue in issues:
        data.append({
            "id": issue.id,
            "title": issue.title,
            "description": issue.description,
            "status": issue.status,
            "created_at": issue.created_at,
        })

    return JsonResponse({
        "issues": data
    }, status=200)

# admin can delete the issue 

@csrf_exempt
def admin_delete_issue(request, issue_id):
    #  Allow only DELETE (or POST if preferred)
    if request.method != "DELETE":
        return JsonResponse({"error": "DELETE method required"}, status=405)

    # Authenticate admin
    user = get_user_from_token(request)
    if not user or (
    user.get("role") != "admin"
    and not user.get("is_super_admin")
    ):
     return JsonResponse({"error": "Admin only"}, status=403)

    #  Get issue
    try:
        issue = Issue.objects.get(id=issue_id)
    except Issue.DoesNotExist:
        return JsonResponse({"error": "Issue not found"}, status=404)

    # Delete issue
    issue.delete()

    #  Success response
    return JsonResponse(
        {"message": "Issue deleted successfully"},
        status=200
    )




