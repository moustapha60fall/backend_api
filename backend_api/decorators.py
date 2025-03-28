# decorators.py

from django.http.response import JsonResponse
from rest_framework.exceptions import PermissionDenied
from functools import wraps

def keycloak_roles(access_roles: list):
    """Décorateur pour restreindre l'accès aux vues en fonction des rôles Keycloak."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_func(*args, **kwargs):
            # Vérifier si la vue est une classe basée sur APIView
            if hasattr(args[0], 'request'):
                request = args[0].request  # Pour les vues basées sur des classes (APIView)
            else:
                request = args[0]  # Pour les vues fonctionnelles classiques
            
            # Vérifier si `request.roles` est bien défini
            if not hasattr(request, 'roles') or not isinstance(request.roles, list):
                return JsonResponse({'detail': "Rôles non définis dans la requête"}, status=403)

            # Vérification des rôles
            if len(set(request.roles) & set(access_roles)) == 0:
                return JsonResponse({'detail': PermissionDenied.default_detail}, status=PermissionDenied.status_code)

            return view_func(*args, **kwargs)

        return wrapped_func

    return decorator
