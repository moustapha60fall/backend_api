# permissions.py


from rest_framework.permissions import BasePermission
from keycloak.exceptions import KeycloakAuthenticationError
from backend_api.settings import keycloak_openid

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return False
        
        try:
            token = auth_header.split("Bearer ")[1]
            user_info = keycloak_openid.userinfo(token)
            roles = user_info.get("realm_access", {}).get("roles", [])
            return "ADMIN" in roles  # Remplace "ADMIN" par le nom exact de ton rôle Keycloak
        except (IndexError, KeycloakAuthenticationError):
            return False
