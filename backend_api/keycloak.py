import requests
import logging
from django.conf import settings
from jose import jwt, JWTError
from api.models import Utilisateur, Role
from django.utils.timezone import now

LOGGER = logging.getLogger(__name__)

class KeycloakConnect:
    def __init__(self):
        config = settings.KEYCLOAK_CONFIG
        self.server_url = config['KEYCLOAK_SERVER_URL']
        self.realm = config['KEYCLOAK_REALM']
        self.client_id = config['KEYCLOAK_CLIENT_ID']
        self.client_secret_key = config['KEYCLOAK_CLIENT_SECRET_KEY']
        self.local_decode = config.get('LOCAL_DECODE', False)

    def decode_token(self, token):
        """Décode le token JWT sans vérifier la signature."""
        try:
            decoded = jwt.decode(
                token, 
                key='',
                options={"verify_signature": False, "verify_aud": False}  
            )
            LOGGER.info(f"Token décodé avec succès: {decoded}")
            return decoded
        except JWTError as e:
            LOGGER.error(f"Erreur de décodage du token: {e}")
            return None

    def get_user_roles(self, token):
        """Récupère les rôles utilisateur depuis le token et filtre les inutiles."""
        decoded = self.decode_token(token)
        if not decoded:
            return None

        # Récupération des rôles
        realm_roles = decoded.get("realm_access", {}).get("roles", [])
        resource_access = decoded.get("resource_access", {})

        client_roles = []
        for client, access in resource_access.items():
            client_roles.extend(access.get("roles", []))

        all_roles = set(realm_roles + client_roles)

        # Filtrage des rôles non nécessaires
        excluded_roles = {"uma_authorization", "offline_access", "default-roles-my-realm", "view-profile", "manage-account-links", "manage-account"}
        filtered_roles = list(all_roles - excluded_roles)

        LOGGER.info(f"Rôles utilisateur après filtrage : {filtered_roles}")
        return filtered_roles

    def get_user_info(self, token):
        """Récupère les informations utilisateur depuis le token."""
        decoded = self.decode_token(token)
        if not decoded:
            LOGGER.error("Erreur : Impossible de décoder le token")
            return None

        user_info = {
            "id": decoded.get("sub"),
            "email": decoded.get("email"),
            "email_verified": decoded.get("email_verified"),
            "given_name": decoded.get("given_name"),
            "family_name": decoded.get("family_name"),
            "username": decoded.get("preferred_username"),
        }

        LOGGER.info(f"Infos utilisateur récupérées : {user_info}")
        return user_info

    def create_or_update_user(self, token):
        """Crée ou met à jour un utilisateur à partir du token Keycloak."""
        decoded = self.decode_token(token)
        if not decoded:
            LOGGER.error("Impossible de créer ou mettre à jour l'utilisateur: Token invalide")
            return None

        email = decoded.get("email")
        username = decoded.get("preferred_username")
        given_name = decoded.get("given_name", "")
        family_name = decoded.get("family_name", "")
        email_verified = decoded.get("email_verified", False)
        roles = self.get_user_roles(token)

        # Récupération ou création de l'utilisateur
        user, created = Utilisateur.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": given_name,
                "last_name": family_name,
                "email_verified": email_verified,
            }
        )

        # Mise à jour des champs modifiables si l'utilisateur existait déjà
        if not created:
            user.email = email
            user.first_name = given_name
            user.last_name = family_name
            user.email_verified = email_verified
            user.last_login = now()
            user.set_unusable_password()
            user.save()

        # Gestion des rôles
        user.roles.clear()  # Supprime les anciens rôles avant de les réattribuer
        for role_name in roles:
            role, _ = Role.objects.get_or_create(nom_role=role_name)
            user.roles.add(role)

        LOGGER.info(f"Utilisateur {'créé' if created else 'mis à jour'} : {user}")
        return user

    def is_token_valid(self, token):
        url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/userinfo"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        
        LOGGER.info(f"Validation token: {response.status_code}, Response: {response.text}")
        
        return response.status_code == 200

