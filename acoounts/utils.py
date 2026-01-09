import jwt
from django.conf import settings

def get_user_from_token(request):
    token = request.COOKIES.get("token")

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except:
        return None
