import logging
from django.conf import settings
from django.http import JsonResponse
from .keycloak import KeycloakConnect
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

LOGGER = logging.getLogger(__name__)

class KeycloakMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.keycloak = KeycloakConnect()

    def __call__(self, request):
        request.roles = []
        request.userinfo = {}

        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return JsonResponse(
                {"detail": NotAuthenticated.default_detail},
                status=NotAuthenticated.status_code
            )

        token = auth_header.split()[1] if " " in auth_header else auth_header

        if not self.keycloak.is_token_valid(token):
            return JsonResponse(
                {"detail": "Token invalide ou expiré."},
                status=AuthenticationFailed.status_code
            )

        request.roles = self.keycloak.get_user_roles(token)
        request.userinfo = self.keycloak.get_user_info(token)

        # Log pour voir si les données sont bien remplies
        LOGGER.info(f"Middleware - User Info: {request.userinfo}")
        LOGGER.info(f"Middleware - User Roles: {request.roles}")

        return self.get_response(request)

