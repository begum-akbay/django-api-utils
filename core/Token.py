from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
import uuid, secrets
from . import Constants

COOKIE_AUTH_DATA = {
    "samesite": "None",
    "secure": True
}


def create(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def set_token_in_cookies(response, token_data):
    response.set_cookie(
        Constants.X_AUTH_REFRESH_TOKEN,
        token_data["refresh"],
        httponly=True,
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
        path="/user",  # only send refresh cookie when calling use endpoints
        **COOKIE_AUTH_DATA
    )

    response.set_cookie(
        Constants.X_AUTH_ACCESS_TOKEN,
        token_data["access"],
        httponly=True,
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
        **COOKIE_AUTH_DATA
    )
    return response


def delete_cookies(response):
    set_token_in_cookies(
        response,
        {
            "access": "",
            "refresh": ""
        }
    )
    return response


def unique():
    return uuid.UUID(bytes=secrets.token_bytes(16))
