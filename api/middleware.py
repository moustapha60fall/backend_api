from django.http import JsonResponse
from keycloak.exceptions import KeycloakAuthenticationError
from backend_api.settings import keycloak_openid

class KeycloakMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JsonResponse({"error": "Authorization token required"}, status=401)

        try:
            token = auth_header.split("Bearer ")[1]
            keycloak_openid.userinfo(token)
        except (IndexError, KeycloakAuthenticationError):
            return JsonResponse({"error": "Invalid token"}, status=401)

        return self.get_response(request)
