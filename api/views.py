from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .constants import CRUD, ServerResponses
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from rest_framework import status
from backend_api.decorators import keycloak_roles
from backend_api.keycloak import KeycloakConnect
import logging
from api.serializers import *
from api.models import *


# Create your views here.

LOGGER = logging.getLogger(__name__)

class UserInfoView(APIView):
    """Endpoint qui retourne les informations utilisateur pour le frontend"""
    
    @keycloak_roles(['USER'])
    def get(self, request):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if not token:
            return Response({"message": "Token manquant"}, status=401)

        keycloak = KeycloakConnect()
        user = keycloak.create_or_update_user(token)

        if not user:
            return Response({"message": "Erreur lors de la récupération de l'utilisateur"}, status=500)

        serializer = UtilisateurSerializer(user)
        return Response(serializer.data)
    

class UpdateUserInfoView(APIView):
    """
    Vue pour mettre à jour les informations utilisateur.
    L'utilisateur doit être authentifié via Keycloak.
    """

    @keycloak_roles(['USER'])
    def put(self, request, _idUtilisateur):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if not token:
            return Response({"message": "Token manquant"}, status=401)

        # Récupérer l'utilisateur authentifié depuis Keycloak
        keycloak = KeycloakConnect()
        user = keycloak.create_or_update_user(token)

        if not user:
            return Response({"message": "Erreur lors de la récupération de l'utilisateur"}, status=500)

        # Vérifier si l'utilisateur existe dans la base de données
        try:
            utilisateur = Utilisateur.objects.get(id_utilisateur=user.id_utilisateur)
        except Utilisateur.DoesNotExist:
            return Response({"message": "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)

        # Sérialiser et mettre à jour les données
        serializer = UtilisateurSerializer(utilisateur, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PhotoUpdateView(APIView):
    """
    Endpoint pour mettre à jour la photo de profil d'un utilisateur.
    """
    parser_classes = (MultiPartParser, FormParser)

    @keycloak_roles(['USER'])
    def post(self, request):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if not token:
            return Response({"message": "Token manquant"}, status=401)

        # Récupérer l'utilisateur depuis Keycloak
        keycloak = KeycloakConnect()
        user = keycloak.create_or_update_user(token)

        if not user:
            return Response({"message": "Erreur lors de la récupération de l'utilisateur"}, status=500)

        # Vérifier si l'utilisateur existe dans la base de données
        try:
            utilisateur = Utilisateur.objects.get(id_utilisateur=user.id_utilisateur)
        except Utilisateur.DoesNotExist:
            return Response({"message": "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)

        # Vérifier si un fichier a été envoyé
        if 'photo_profil' not in request.FILES:  # Remplacez ici aussi
            return Response({"message": "Aucun fichier envoyé"}, status=400)

        # Supprimer l'ancienne image si elle existe
        if utilisateur.photo_profil:  # Remplacez ici
            default_storage.delete(utilisateur.photo_profil.path)

        # Enregistrer la nouvelle image
        utilisateur.photo_profil = request.FILES['photo_profil']  # Remplacez ici
        utilisateur.save()

        return Response({"message": "Photo de profil mise à jour avec succès", "photo_profil": utilisateur.photo_profil.url}, status=200)
    
class RolesListView(ListAPIView):
    """Endpoint pour récupérer la liste des pays"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

#----------------------------------------------------------------------------------------------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@keycloak_roles(['ADMIN'])
def manage_utilisateur(request, _id_utilisateur=0):
    try:        
        if request.method == 'GET':  # READ
            # Récupérer TOUS les utilisateurs si aucun ID n'est fourni
            if _id_utilisateur == 0:
                utilisateurs = Utilisateur.objects.all().order_by('last_name', 'first_name')
                serializer = UtilisateurSerializer(utilisateurs, many=True)
                return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)
            
            # Récupérer un utilisateur spécifique
            utilisateur = get_object_or_404(Utilisateur, pk=_id_utilisateur)
            serializer = UtilisateurSerializer(utilisateur)
            return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)        

        elif request.method == 'POST':  # CREATE
            serializer = UtilisateurSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 1, 'msg': ServerResponses.ADD_SUCCESS}, status=status.HTTP_201_CREATED)
            return Response({'status': 'error', 'code': -502, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':  # UPDATE
            utilisateur = get_object_or_404(Utilisateur, pk=_id_utilisateur)
            serializer = UtilisateurSerializer(utilisateur, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 2, 'msg': ServerResponses.UPDATE_SUCCESS}, status=status.HTTP_200_OK)
            return Response({'status': 'error', 'code': -503, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':  # DELETE
            utilisateur = get_object_or_404(Utilisateur, pk=_id_utilisateur)
            utilisateur.delete()
            return Response({'status': 'success', 'code': 3, 'msg': ServerResponses.DELETE_SUCCESS}, status=status.HTTP_200_OK)

        else:
            return Response({'status': 'error', 'code': -506, 'msg': ServerResponses.getErrorMessage(506)}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'code': -510, 'msg': ServerResponses.getErrorMessage(510)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@keycloak_roles(['ADMIN'])
def manage_etudiant(request, _id_etudiant=0):
    try:        
        if request.method == 'GET':  # READ
            # Récupérer TOUS les étudiants si aucun ID n'est fourni
            if _id_etudiant == 0:
                etudiants = Etudiant.objects.all().order_by('matricule')
                serializer = EtudiantSerializer(etudiants, many=True)
                return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)
            
            # Récupérer un étudiant spécifique
            etudiant = get_object_or_404(Etudiant, pk=_id_etudiant)
            serializer = EtudiantSerializer(etudiant)
            return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)        

        elif request.method == 'POST':  # CREATE
            serializer = EtudiantSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 1, 'msg': ServerResponses.ADD_SUCCESS}, status=status.HTTP_201_CREATED)
            return Response({'status': 'error', 'code': -502, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':  # UPDATE
            etudiant = get_object_or_404(Etudiant, pk=_id_etudiant)
            serializer = EtudiantSerializer(etudiant, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 2, 'msg': ServerResponses.UPDATE_SUCCESS}, status=status.HTTP_200_OK)
            return Response({'status': 'error', 'code': -503, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':  # DELETE
            etudiant = get_object_or_404(Etudiant, pk=_id_etudiant)
            etudiant.delete()
            return Response({'status': 'success', 'code': 3, 'msg': ServerResponses.DELETE_SUCCESS}, status=status.HTTP_200_OK)

        else:
            return Response({'status': 'error', 'code': -506, 'msg': ServerResponses.getErrorMessage(506)}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'code': -510, 'msg': ServerResponses.getErrorMessage(510)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@keycloak_roles(['ADMIN'])
def manage_enseignant(request, _id_enseignant=0):
    try:        
        if request.method == 'GET':  # READ
            # Récupérer TOUS les enseignants si aucun ID n'est fourni
            if _id_enseignant == 0:
                enseignants = Enseignant.objects.all().order_by('utilisateur__last_name', 'utilisateur__first_name')
                serializer = EnseignantSerializer(enseignants, many=True)
                return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)
            
            # Récupérer un enseignant spécifique
            enseignant = get_object_or_404(Enseignant, pk=_id_enseignant)
            serializer = EnseignantSerializer(enseignant)
            return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)        

        elif request.method == 'POST':  # CREATE
            serializer = EnseignantSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 1, 'msg': ServerResponses.ADD_SUCCESS}, status=status.HTTP_201_CREATED)
            return Response({'status': 'error', 'code': -502, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':  # UPDATE
            enseignant = get_object_or_404(Enseignant, pk=_id_enseignant)
            serializer = EnseignantSerializer(enseignant, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 2, 'msg': ServerResponses.UPDATE_SUCCESS}, status=status.HTTP_200_OK)
            return Response({'status': 'error', 'code': -503, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':  # DELETE
            enseignant = get_object_or_404(Enseignant, pk=_id_enseignant)
            enseignant.delete()
            return Response({'status': 'success', 'code': 3, 'msg': ServerResponses.DELETE_SUCCESS}, status=status.HTTP_200_OK)

        else:
            return Response({'status': 'error', 'code': -506, 'msg': ServerResponses.getErrorMessage(506)}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'code': -510, 'msg': ServerResponses.getErrorMessage(510)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@keycloak_roles(['ADMIN'])
def manage_classe(request, _id_classe=0):
    try:
        if request.method == 'GET':  # READ
            # Récupérer TOUS les classes si aucun ID n'est fourni
            if _id_classe == 0:
                classes = Classe.objects.all().order_by('code_classe')
                serializer = ClasseSerializer(classes, many=True)
                return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)
            
            # Récupérer une classe spécifique
            classe = get_object_or_404(Classe, pk=_id_classe)
            serializer = ClasseSerializer(classe)
            return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)        

        elif request.method == 'POST':  # CREATE
            serializer = ClasseSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 1, 'msg': ServerResponses.ADD_SUCCESS}, status=status.HTTP_201_CREATED)
            return Response({'status': 'error', 'code': -502, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':  # UPDATE
            classe = get_object_or_404(Classe, pk=_id_classe)
            serializer = ClasseSerializer(classe, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 2, 'msg': ServerResponses.UPDATE_SUCCESS}, status=status.HTTP_200_OK)
            return Response({'status': 'error', 'code': -503, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':  # DELETE
            classe = get_object_or_404(Classe, pk=_id_classe)
            classe.delete()
            return Response({'status': 'success', 'code': 3, 'msg': ServerResponses.DELETE_SUCCESS}, status=status.HTTP_200_OK)

        else:
            return Response({'status': 'error', 'code': -506, 'msg': ServerResponses.getErrorMessage(506)}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'code': -510, 'msg': ServerResponses.getErrorMessage(510)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@keycloak_roles(['ADMIN'])
def manage_inscription(request, _id_inscription=0):
    try:
        if request.method == 'GET':  # READ
            # Récupérer TOUS les inscriptions si aucun ID n'est fourni
            if _id_inscription == 0:
                inscriptions = Inscription.objects.all().order_by('date_inscription')
                serializer = InscriptionSerializer(inscriptions, many=True)
                return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)
            
            # Récupérer une inscription spécifique
            inscription = get_object_or_404(Inscription, pk=_id_inscription)
            serializer = InscriptionSerializer(inscription)
            return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)        

        elif request.method == 'POST':  # CREATE
            serializer = InscriptionSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 1, 'msg': ServerResponses.ADD_SUCCESS}, status=status.HTTP_201_CREATED)
            return Response({'status': 'error', 'code': -502, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':  # UPDATE
            inscription = get_object_or_404(Inscription, pk=_id_inscription)
            serializer = InscriptionSerializer(inscription, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 2, 'msg': ServerResponses.UPDATE_SUCCESS}, status=status.HTTP_200_OK)
            return Response({'status': 'error', 'code': -503, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':  # DELETE
            inscription = get_object_or_404(Inscription, pk=_id_inscription)
            inscription.delete()
            return Response({'status': 'success', 'code': 3, 'msg': ServerResponses.DELETE_SUCCESS}, status=status.HTTP_200_OK)

        else:
            return Response({'status': 'error', 'code': -506, 'msg': ServerResponses.getErrorMessage(506)}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'code': -510, 'msg': ServerResponses.getErrorMessage(510)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@keycloak_roles(['ADMIN'])
def manage_ue(request, _id_ue=0):
    try:
        if request.method == 'GET':  # READ
            # Récupérer TOUS les unités d'enseignement si aucun ID n'est fourni
            if _id_ue == 0:
                ues = UE.objects.all().order_by('code_ue')
                serializer = UESerializer(ues, many=True)
                return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)

            # Récupérer une unité d'enseignement spécifique
            ue = get_object_or_404(UE, pk=_id_ue)
            serializer = UESerializer(ue)
            return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)

        elif request.method == 'POST':  # CREATE
            serializer = UESerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 1, 'msg': ServerResponses.ADD_SUCCESS}, status=status.HTTP_201_CREATED)
            return Response({'status': 'error', 'code': -502, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':  # UPDATE
            ue = get_object_or_404(UE, pk=_id_ue)
            serializer = UESerializer(ue, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 2, 'msg': ServerResponses.UPDATE_SUCCESS}, status=status.HTTP_200_OK)
            return Response({'status': 'error', 'code': -503, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':  # DELETE
            ue = get_object_or_404(UE, pk=_id_ue)
            ue.delete()
            return Response({'status': 'success', 'code': 3, 'msg': ServerResponses.DELETE_SUCCESS}, status=status.HTTP_200_OK)

        else:
            return Response({'status': 'error', 'code': -506, 'msg': ServerResponses.getErrorMessage(506)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'code': -510, 'msg': ServerResponses.getErrorMessage(510)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@keycloak_roles(['ADMIN'])
def manage_ec(request, _id_ec=0):
    try:
        if request.method == 'GET':  # READ
            # Récupérer TOUS les éléments constitutifs si aucun ID n'est fourni
            if _id_ec == 0:
                ecs = EC.objects.all().order_by('ue__code_ue', 'code_ec')
                serializer = ECSerializer(ecs, many=True)
                return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)

            # Récupérer un élément constitutif spécifique
            ec = get_object_or_404(EC, pk=_id_ec)
            serializer = ECSerializer(ec)
            return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)

        elif request.method == 'POST':  # CREATE
            serializer = ECSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 1, 'msg': ServerResponses.ADD_SUCCESS}, status=status.HTTP_201_CREATED)
            return Response({'status': 'error', 'code': -502, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':  # UPDATE
            ec = get_object_or_404(EC, pk=_id_ec)
            serializer = ECSerializer(ec, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 2, 'msg': ServerResponses.UPDATE_SUCCESS}, status=status.HTTP_200_OK)
            return Response({'status': 'error', 'code': -503, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':  # DELETE
            ec = get_object_or_404(EC, pk=_id_ec)
            ec.delete()
            return Response({'status': 'success', 'code': 3, 'msg': ServerResponses.DELETE_SUCCESS}, status=status.HTTP_200_OK)

        else:
            return Response({'status': 'error', 'code': -506, 'msg': ServerResponses.getErrorMessage(506)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'code': -510, 'msg': ServerResponses.getErrorMessage(510)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@keycloak_roles(['ADMIN'])
def manage_session(request, _id_session=0):
    try:
        if request.method == 'GET':  # READ
            # Récupérer TOUTES les sessions d'examen si aucun ID n'est fourni
            if _id_session == 0:
                sessions = SessionExamen.objects.all().order_by('-annee_universitaire', 'type_session')
                serializer = SessionExamenSerializer(sessions, many=True)
                return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)

            # Récupérer une session d'examen spécifique
            session = get_object_or_404(SessionExamen, pk=_id_session)
            serializer = SessionExamenSerializer(session)
            return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)

        elif request.method == 'POST':  # CREATE
            serializer = SessionExamenSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 1, 'msg': ServerResponses.ADD_SUCCESS}, status=status.HTTP_201_CREATED)
            return Response({'status': 'error', 'code': -502, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':  # UPDATE
            session = get_object_or_404(SessionExamen, pk=_id_session)
            serializer = SessionExamenSerializer(session, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 2, 'msg': ServerResponses.UPDATE_SUCCESS}, status=status.HTTP_200_OK)
            return Response({'status': 'error', 'code': -503, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':  # DELETE
            session = get_object_or_404(SessionExamen, pk=_id_session)
            session.delete()
            return Response({'status': 'success', 'code': 3, 'msg': ServerResponses.DELETE_SUCCESS}, status=status.HTTP_200_OK)

        else:
            return Response({'status': 'error', 'code': -506, 'msg': ServerResponses.getErrorMessage(506)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'code': -510, 'msg': ServerResponses.getErrorMessage(510)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@keycloak_roles(['ADMIN'])
def manage_note(request, _id_note=0):
    try:
        if request.method == 'GET':  # READ
            # Récupérer TOUTES les notes si aucun ID n'est fourni
            if _id_note == 0:
                notes = Note.objects.all().order_by('etudiant__matricule', 'ec__code_ec')
                serializer = NoteSerializer(notes, many=True)
                return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)

            # Récupérer une note spécifique
            note = get_object_or_404(Note, pk=_id_note)
            serializer = NoteSerializer(note)
            return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)

        elif request.method == 'POST':  # CREATE
            serializer = NoteSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 1, 'msg': ServerResponses.ADD_SUCCESS}, status=status.HTTP_201_CREATED)
            return Response({'status': 'error', 'code': -502, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':  # UPDATE
            note = get_object_or_404(Note, pk=_id_note)
            serializer = NoteSerializer(note, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'code': 2, 'msg': ServerResponses.UPDATE_SUCCESS}, status=status.HTTP_200_OK)
            return Response({'status': 'error', 'code': -503, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':  # DELETE
            note = get_object_or_404(Note, pk=_id_note)
            note.delete()
            return Response({'status': 'success', 'code': 3, 'msg': ServerResponses.DELETE_SUCCESS}, status=status.HTTP_200_OK)

        else:
            return Response({'status': 'error', 'code': -506, 'msg': ServerResponses.getErrorMessage(506)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'code': -510, 'msg': ServerResponses.getErrorMessage(510)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
@api_view(['GET'])
@keycloak_roles(['ADMIN'])
def get_etudiants_by_classe_annee(request, id_classe, annee_academique):
    try:
        inscriptions = Inscription.objects.filter(classe_id=id_classe, annee_academique=annee_academique)
        etudiants = [inscription.etudiant for inscription in inscriptions]
        serializer = EtudiantSerializer(etudiants, many=True)
        
        return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)
    
    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'code': -510, 'msg': ServerResponses.getErrorMessage(510)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
@api_view(['GET'])
@keycloak_roles(['ADMIN', 'ETUDIANT'])
def get_notes_by_etudiant(request, id_etudiant):
    try:
        # Filtrer les notes via le champ de clé étrangère
        notes = Note.objects.filter(etudiant__id_etudiant=id_etudiant)
        serializer = NoteSerializer(notes, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)
    except Exception as exc:
        print(exc)
        return Response({'status': 'error', 'msg': 'Erreur lors de la récupération des notes'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------------------------------------------------------------
