from rest_framework import serializers
from .models import *

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'
        extra_kwargs = {
            'nom_role': {'help_text': "Libellé du rôle (ex: Administrateur, Enseignant)"}
        }

class UtilisateurSerializer(serializers.ModelSerializer):
    roles = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), many=True)

    class Meta:
        model = Utilisateur
        fields = [
            'id_utilisateur', 
            'username', 
            'first_name', 
            'last_name', 
            'email', 
            'sexe', 
            'telephone', 
            'date_naissance', 
            'photo_profil', 
            'address_profil', 
            'newsletter_abonne', 
            'blog_posts', 
            'roles',
            'date_joined',
            'last_login'
        ]

class EtudiantSerializer(serializers.ModelSerializer):
    utilisateur = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.all())

    utilisateur_details = serializers.SerializerMethodField(
        read_only=True,
        help_text="Détails complets de l'utilisateur associé"
    )
    
    class Meta:
        model = Etudiant
        fields = ['id_etudiant', 'utilisateur', 'matricule', 'utilisateur_details']

    def create(self, validated_data):
        etudiant = Etudiant.objects.create(**validated_data)
        return etudiant
    
    def get_utilisateur_details(self, obj):
        """Récupère les détails de l'utilisateur si disponible"""
        if obj.utilisateur:
            return {
                "id_utilisateur": obj.utilisateur.id_utilisateur,
                "username": obj.utilisateur.username,
                "email": obj.utilisateur.email,
                "first_name": obj.utilisateur.first_name,
                "last_name": obj.utilisateur.last_name,
            }
        return None

class EnseignantSerializer(serializers.ModelSerializer):
    utilisateur = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.all())

    titre_display = serializers.CharField(
        source='get_titre_display', 
        read_only=True,
        help_text="Libellé complet du titre académique"
    )

    utilisateur_details = serializers.SerializerMethodField(
        read_only=True,
        help_text="Détails complets de l'utilisateur associé"
    )
    
    class Meta:
        model = Enseignant
        fields = ['id_enseignant', 'utilisateur', 'titre', 'specialite', 'utilisateur_details', 'titre_display']

    def create(self, validated_data):
        enseignant = Enseignant.objects.create(**validated_data)
        return enseignant

    def get_utilisateur_details(self, obj):
        """Récupère les détails de l'utilisateur si disponible"""
        if obj.utilisateur:
            return {
                "id_utilisateur": obj.utilisateur.id_utilisateur,
                "username": obj.utilisateur.username,
                "email": obj.utilisateur.email,
                "first_name": obj.utilisateur.first_name,
                "last_name": obj.utilisateur.last_name,
            }
        return None

class ClasseSerializer(serializers.ModelSerializer):
    code_classe = serializers.CharField(
        read_only=False,
        help_text="Généré automatiquement à partir des autres champs"
    )
    filiere_display = serializers.CharField(
        source='get_filiere_display', 
        read_only=True,
        help_text="Intitulé complet de la formation"
    )
    class Meta:
        model = Classe
        fields = [
            'id_classe', 
            'code_classe', 
            'filiere_display', 
            'filiere', 
            'niveau', 
            'option', 
            'annee'
        ]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Classe.objects.all(),
                fields=['filiere', 'niveau', 'option', 'annee'],
                message="Cette combinaison existe déjà"
            )
        ]

class InscriptionSerializer(serializers.ModelSerializer):
    etudiant = serializers.PrimaryKeyRelatedField(queryset=Etudiant.objects.all())
    
    classe = serializers.PrimaryKeyRelatedField(queryset=Classe.objects.all())
    
    utilisateur_details = serializers.SerializerMethodField(
        read_only=True,
        help_text="Détails complets de l'utilisateur associé"
    )
    
    classe_details = serializers.SerializerMethodField(
        read_only=True,
        help_text="Détails complets de la classe associé"
    )
    
    class Meta:
        model = Inscription
        fields = '__all__'
        read_only_fields = ['date_inscription']
        
    def create(self, validated_data):
        inscription = Inscription.objects.create(**validated_data)
        return inscription
    
    def get_utilisateur_details(self, obj):
        """Récupère les détails de l'utilisateur via l'étudiant si disponible"""
        if obj.etudiant and hasattr(obj.etudiant, 'utilisateur'):
            return {
                "id_utilisateur": obj.etudiant.utilisateur.id_utilisateur,
                "username": obj.etudiant.utilisateur.username,
                "email": obj.etudiant.utilisateur.email,
                "first_name": obj.etudiant.utilisateur.first_name,
                "last_name": obj.etudiant.utilisateur.last_name,
            }
        return None
    
    def get_classe_details(self, obj):
        """Récupère les détails de l'utilisateur si disponible"""
        if obj.classe:
            return {
                "id_classe": obj.classe.id_classe,
                "code_classe": obj.classe.code_classe,
            }
        return None
            
class UESerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UE
        fields = [
            'id_ue', 
            'code_ue', 
            'intitule', 
            'credits_ects', 
            'semestre'
        ]
        read_only_fields = ['id_ue']

    def create(self, validated_data):
        """Créer une nouvelle unité d'enseignement"""
        ue = UE(**validated_data)
        ue.save()
        return ue

class ECSerializer(serializers.ModelSerializer):
    ue = serializers.PrimaryKeyRelatedField(queryset=UE.objects.all())
    responsable = serializers.PrimaryKeyRelatedField(queryset=Enseignant.objects.all())

    ue_details = serializers.SerializerMethodField(
        read_only=True,
        help_text="Détails complets de l'utilisateur associé"
    )

    enseignant_details = serializers.SerializerMethodField(
        read_only=True,
        help_text="Détails complets de l'utilisateur associé"
    )
        
    class Meta:
        model = EC
        fields = [
            'id_ec', 
            'ue', 
            'code_ec', 
            'intitule_ec', 
            'coefficient',
            'responsable',
            'ue_details',
            'enseignant_details'
        ]
        read_only_fields = ['id_ec']  # Rendre id_ec en lecture seule

    def create(self, validated_data):
        """Créer un nouvel élément constitutif"""
        ec = EC(**validated_data)
        ec.save()
        return ec
    
    def get_ue_details(self, obj):
        """Récupère les détails de l'utilisateur si disponible"""
        if obj.ue:
            return {
                "id_ue": obj.ue.id_ue,
                "code_ue": obj.ue.code_ue,
                "credits_ects": obj.ue.credits_ects,
                "semestre": obj.ue.semestre,
                "intitule_ue": obj.ue.intitule,
            }
        return None
    
    def get_enseignant_details(self, obj):
        """Récupère les détails de l'utilisateur via l'étudiant si disponible"""
        if obj.responsable and hasattr(obj.responsable, 'utilisateur'):
            return {
                "id_utilisateur": obj.responsable.utilisateur.id_utilisateur,
                "username": obj.responsable.utilisateur.username,
                "email": obj.responsable.utilisateur.email,
                "first_name": obj.responsable.utilisateur.first_name,
                "last_name": obj.responsable.utilisateur.last_name,
            }
        return None

class SessionExamenSerializer(serializers.ModelSerializer):
    code_session = serializers.CharField(read_only=True)

    class Meta:
        model = SessionExamen
        fields = '__all__'
        extra_kwargs = {
            'date_fin': {'help_text': "Doit être postérieure à la date de début"}
        }

    def validate(self, data):
        if data['date_debut'] > data['date_fin']:
            raise serializers.ValidationError("La date de fin doit être postérieure à la date de début")
        return data

class NoteSerializer(serializers.ModelSerializer):
    etudiant = serializers.PrimaryKeyRelatedField(queryset=Etudiant.objects.all())

    ec = serializers.PrimaryKeyRelatedField(queryset=EC.objects.all())

    session = serializers.PrimaryKeyRelatedField(queryset=SessionExamen.objects.all())

    etudiant_details = serializers.SerializerMethodField(
        read_only=True,
        help_text="Détails complets de l'utilisateur associé"
    )
    
    ec_details = serializers.SerializerMethodField(
        read_only=True,
        help_text="Détails complets de l'utilisateur associé"
    )

    session_details = serializers.SerializerMethodField(
        read_only=True,
        help_text="Détails complets de l'utilisateur associé"
    )    
    
    moyenne_ue = serializers.SerializerMethodField(
        help_text="Moyenne pondérée dans l'UE"
    )

    class Meta:
        model = Note
        fields =[
            'id_note', 
            'etudiant', 
            'ec', 
            'session', 
            'valeur', 
            'moyenne_ue',
            'date_validation', 
            'etudiant_details', 
            'ec_details', 
            'session_details'
        ]
        read_only_fields = ('date_validation','moyenne_ue')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Note.objects.all(),
                fields=['etudiant', 'ec', 'session'],
                message="Une note existe déjà pour cette combinaison"
            )
        ]
        
    def get_etudiant_details(self, obj):
        """Récupère les détails de l'utilisateur via l'étudiant si disponible"""
        if obj.etudiant and hasattr(obj.etudiant, 'utilisateur'):
            return {
                "id_utilisateur": obj.etudiant.utilisateur.id_utilisateur,
                "username": obj.etudiant.utilisateur.username,
                "email": obj.etudiant.utilisateur.email,
                "first_name": obj.etudiant.utilisateur.first_name,
                "last_name": obj.etudiant.utilisateur.last_name,
            }
        return None
    
    def get_ec_details(self, obj):
        """Récupère les détails de l'utilisateur si disponible"""
        if obj.ec:
            return {
                "id_ec": obj.ec.id_ec,
                "code_ec": obj.ec.code_ec,
                "intitule_ec": obj.ec.intitule_ec,
                "coefficient": obj.ec.coefficient,
                "id_ue": obj.ec.ue.id_ue,
                "code_ue": obj.ec.ue.code_ue,
                "credits_ects": obj.ec.ue.credits_ects,
                "semestre": obj.ec.ue.semestre,
                "intitule_ue": obj.ec.ue.intitule
            }
        return None

    def get_session_details(self, obj):
        """Récupère les détails de l'utilisateur si disponible"""
        if obj.session:
            return {
                "id_session": obj.session.id_session,
                "code_session": obj.session.code_session,
                "annee_universitaire": obj.session.annee_universitaire,
                "type_session": obj.session.type_session,
            }
        return None

    def get_moyenne_ue(self, obj):
        return obj.ec.ue.calculer_moyenne(obj.etudiant)
