from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator

# Create your models here.

class Role(models.Model):
    id_role = models.AutoField(
        db_column='id_role', 
        primary_key=True,
        db_comment="Identifiant unique auto-incrémenté du rôle"
    )
    nom_role = models.CharField(
        db_column='nom_role', 
        max_length=100, 
        unique=True,
        db_comment="Libellé du rôle (ex: Administrateur, Enseignant)"
    )

    def __str__(self):
        return self.nom_role

    class Meta:
        ordering = ['nom_role']
        db_table = 'roles'
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"
        managed = True 

class Utilisateur(AbstractUser):
    GENRE_CHOICES = [('H', 'Homme'), ('F', 'Femme')]
    
    id_utilisateur = models.AutoField(
        primary_key=True,
        db_column='id_utilisateur',
        db_comment="Identifiant unique de l'utilisateur"
    )
    roles = models.ManyToManyField(
        Role, 
        through='UtilisateurRole',
        related_name='utilisateurs',
        db_comment="Relation ManyToMany avec les rôles via la table de liaison"
    )    
    sexe = models.CharField(
        max_length=1, 
        choices=GENRE_CHOICES, 
        null=True,
        blank=True,
        db_comment="Genre de l'utilisateur (H=Homme, F=Femme)"
    )
    email_verified = models.BooleanField(
        db_column='email_verified',
        default=False,
        db_comment="Statut de vérification de l'adresse email"
    )
    telephone = models.CharField(
        db_column='telephone',
        max_length=15, 
        blank=True, 
        null=True,
        validators=[RegexValidator(r'^\+?[0-9]{8,15}$')],
        db_comment="Numéro de téléphone au format international"
    )
    date_naissance = models.DateField(
        db_column='date_naissance',
        blank=True, 
        null=True,
        db_comment="Date de naissance au format AAAA-MM-JJ"
    )
    photo_profil = models.ImageField(
        db_column='photo_profil',
        upload_to='profils/photo/%Y/%m/%d/',
        max_length=255, 
        null=True, 
        blank=True,
        db_comment="Chemin relatif de la photo de profil"
    )
    address_profil = models.TextField(
        db_column='address_profil',
        blank=True,
        null=True,
        db_comment="Adresse postale complète",
        help_text="Rue, code postal, ville, pays"
    )
    newsletter_abonne = models.BooleanField(
        db_column='newsletter_abonne',
        default=False,
        db_comment="Abonnement aux communications"
    )
    blog_posts = models.BooleanField(
        db_column='blog_posts',
        default=False,
        db_comment="Abonnement aux communications"
    )        

    # Override des champs Django par défaut
    groups = models.ManyToManyField(
        Group,
        related_name='utilisateurs',
        blank=True,
        verbose_name='groupes',
        db_comment="Groupes d'utilisateurs pour les permissions"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='utilisateurs',
        blank=True,
        verbose_name='permissions',
        db_comment="Permissions spécifiques à l'utilisateur"
    )

    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"

    class Meta:
        ordering = ['last_name', 'first_name']
        db_table = 'utilisateurs'
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['date_joined'])
        ]

class UtilisateurRole(models.Model):
    utilisateur = models.ForeignKey(
        Utilisateur, 
        db_column='id_utilisateur',
        on_delete=models.PROTECT,
        db_comment="Clé étrangère vers la table utilisateurs"
    )
    role = models.ForeignKey(
        Role, 
        db_column='id_role',
        on_delete=models.PROTECT,
        db_comment="Clé étrangère vers la table roles"
    )

    class Meta:
        db_table = 'utilisateur_roles'
        unique_together = (('utilisateur', 'role'),)
        verbose_name = "Affectation rôle"
        verbose_name_plural = "Affectations des rôles"
        db_table_comment = "Table de liaison entre utilisateurs et rôles"

class Etudiant(models.Model):
    id_etudiant = models.AutoField(
        db_column='id_etudiant', 
        primary_key=True,
        db_comment="Identifiant unique auto-incrémenté de l'étudiant"
    )
    utilisateur = models.OneToOneField(
        Utilisateur,
        db_column='id_utilisateur',
        on_delete=models.CASCADE,
        related_name='profil_etudiant',
        null=True,
        blank=True,
        db_comment="Référence au compte utilisateur associé"
    )
    matricule = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9]{8}$')],
        db_comment="Matricule académique unique (8 caractères alphanum)"
    )

    def __str__(self):
        return self.matricule

    class Meta:
        db_table = 'etudiants'
        verbose_name = "Profil étudiant"
        verbose_name_plural = "Profils étudiants"
        indexes = [
            models.Index(fields=['matricule'], name='idx_matricule'),
            models.Index(fields=['utilisateur'], name='idx_etudiant_user')
        ]
        db_table_comment = "Les informations spécifiques aux étudiants"
        
class Enseignant(models.Model):
    TITRES = [
        ('Pr.', 'Professeur'),
        ('Dr.', 'Docteur'),
        ('Mr.', 'Monsieur'),
        ('Mme', 'Madame')
    ]
    
    id_enseignant = models.AutoField(
        db_column='id_enseignant',
        primary_key=True,
        db_comment="Identifiant unique auto-généré de l'enseignant"
    )
    utilisateur = models.OneToOneField(
        'Utilisateur',
        db_column='id_utilisateur',
        on_delete=models.CASCADE,
        related_name='profil_enseignant',
        db_comment="Liaison avec le compte utilisateur principal"
    )  # utilisateur ne doit pas être null
    titre = models.CharField(
        max_length=5,
        choices=TITRES,
        default='Dr.',
        db_comment="Titre académique de l'enseignant"
    ) 
    specialite = models.CharField(
        max_length=100,
        db_comment="Domaine d'expertise principal (ex: Mathématiques Appliquées)",
        help_text="Spécifiez la discipline principale"
    )

    def __str__(self):
        return f"{self.get_titre_display()} {self.utilisateur.get_full_name()}" if self.utilisateur else f"Enseignant {self.id_enseignant}"

    class Meta:
        db_table = 'enseignants'
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"
        indexes = [
            models.Index(fields=['specialite'], name='idx_specialite'),
            models.Index(fields=['titre'], name='idx_titre')
        ]
        db_table_comment = "Regroupe les informations professionnelles des enseignants"

class Classe(models.Model):
    FILIERES = [
        ("MAGA", "Master Analyse Géométrie Algébrique"),
        ("TDSI", "Transmission de Données et Sécurité Informatique"),
        ("MS2E", "Master Sécurité des Systèmes Embarqués"),
    ]
    
    NIVEAUX = [
        ("L", "Licence"),
        ("M", "Master")
    ]

    OPTIONS = [
        ("PROFESSIONNEL", "Professionnel"),
        ("RECHERCHE", "Recherche"),
    ]
    
    id_classe = models.AutoField(
        db_column='id_classe', 
        primary_key=True,
        db_comment="Identifiant unique de la classe"
    )
    code_classe = models.CharField(
        db_column='code_classe',
        max_length=15,
        unique=True,
        db_comment="Code unique de la classe (ex: M1MAGA)"
    )
    filiere = models.CharField(
        max_length=4, 
        choices=FILIERES,
        db_comment="Domaine de spécialisation de la formation"
    )
    niveau = models.CharField(
        max_length=1, 
        choices=NIVEAUX,
        db_comment="Niveau académique (L=Licence, M=Master)"
    )
    option = models.CharField(
        max_length=20, 
        choices=OPTIONS, 
        db_comment="Option de spécialisation de la formation")
    annee = models.PositiveSmallIntegerField(
        db_comment="Année dans le cycle (1 à 5)"
    )
    
    def save(self, *args, **kwargs):
        """ Génère automatiquement le code_classe si non défini """
        if not self.code_classe:
            self.code_classe = f"{self.niveau}{self.annee}{self.filiere}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code_classe     

    class Meta:
        db_table = 'classes'
        verbose_name = "Parcours académique"
        verbose_name_plural = "Parcours académiques"
        constraints = [
            models.UniqueConstraint(
                fields=['filiere', 'niveau', 'option', 'annee'],
                name='unique_parcours'
            )
        ]

class Inscription(models.Model):
    id_inscription = models.AutoField(
        db_column='id_inscription',
        primary_key=True,
        db_comment="Identifiant unique de l'inscription"
    )
    etudiant = models.ForeignKey(
        Etudiant,
        db_column='id_etudiant',
        on_delete=models.PROTECT,
        related_name='inscriptions',
        db_comment="Référence à l'étudiant inscrit"
    )
    classe = models.ForeignKey(
        Classe,
        db_column='id_classe',
        on_delete=models.PROTECT,
        related_name='inscrits',
        db_comment="Référence à la classe concernée"
    )
    date_inscription = models.DateTimeField(
        db_column='date_inscription',
        auto_now_add=True,
        db_comment="Date de la création de l'inscription"
    )
    annee_academique = models.CharField(
        db_column='annee_academique',
        max_length=9,
        validators=[RegexValidator(r'^\d{4}-\d{4}$')],
        db_comment="Année académique au format 'AAAA-AAAA'"
    )

    def __str__(self):
        return f"{self.etudiant.matricule} | {self.classe.code_classe} | {self.annee_academique}"
    
    class Meta:
        db_table = 'inscriptions'
        unique_together = ('etudiant', 'classe', 'annee_academique')
        indexes = [
            models.Index(fields=['classe', 'annee_academique'], name='idx_classe_annee_academique'),
            models.Index(fields=['date_inscription'])
        ]
        verbose_name = "Inscription académique"
        verbose_name_plural = "Inscriptions académiques"
        db_table_comment = "Gestion des inscriptions annuelles aux classes"

class UE(models.Model):
    SEMESTRES = [(1, 'Semestre 1'), (2, 'Semestre 2')]

    id_ue = models.AutoField(
        db_column='id_ue',
        primary_key=True,
        db_comment="Identifiant unique de l'unité d'enseignement"
    )
    code_ue = models.CharField(
        db_column='code_ue',
        max_length=20,
        unique=True,
        db_comment="Code officiel de l'UE"
    )
    intitule = models.CharField(
        db_column='intitule_ue',
        max_length=200,
        db_comment="Intitulé complet de l'unité d'enseignement"
    )
    credits_ects = models.PositiveSmallIntegerField(
        db_column='credits_ects',
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        db_comment="Nombre de crédits ECTS"
    )
    semestre = models.PositiveIntegerField(
        db_column='semestre',
        choices=SEMESTRES,
        db_comment="Semestre d'enseignement"
    )

    def __str__(self):
        return f"{self.code_ue} - {self.intitule}"
    
    def calculer_moyenne(self, etudiant):
        """Calcule la moyenne pondérée des notes de l'étudiant pour cette UE."""
        notes = self.elements_constitutifs.prefetch_related('notes').all()
        total_notes = 0
        total_coefficients = 0

        for ec in notes:
            for note in ec.notes.filter(etudiant=etudiant):
                total_notes += note.valeur * ec.coefficient
                total_coefficients += ec.coefficient

        if total_coefficients > 0:
            return total_notes / total_coefficients
        return 0
    
    class Meta:
        db_table = 'unites_enseignement'
        ordering = ['code_ue']
        indexes = [
            models.Index(fields=['semestre']),
            models.Index(fields=['code_ue', 'semestre'])
        ]
        verbose_name = "Unité d'Enseignement"
        verbose_name_plural = "Unités d'Enseignement"

class EC(models.Model):
    id_ec = models.AutoField(
        db_column='id_ec',
        primary_key=True,
        db_comment="Identifiant unique de l'élément constitutif"
    )
    ue = models.ForeignKey(
        UE,
        db_column='id_ue',
        on_delete=models.CASCADE,
        related_name='elements_constitutifs',
        db_comment="Unité d'enseignement parente"
    )
    code_ec = models.CharField(
        db_column='code_ec',
        max_length=20,
        unique=True,
        db_comment="Code officiel de l'EC"
    )
    intitule_ec = models.CharField(
        db_column='intitule_ec',
        max_length=150,
        db_comment="Intitulé complet de l'élément constitutif"
    )
    coefficient = models.FloatField(
        db_column='coefficient',
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        db_comment="Coefficient dans l'UE"
    )
    responsable = models.ForeignKey(
        'Enseignant',
        db_column='id_responsable',
        on_delete=models.PROTECT,
        related_name='ecs_encadrees',
        db_comment="Enseignant responsable de l'UE"
    )

    def __str__(self):
        return f"{self.code_ec} | Coeff {self.coefficient} | {self.intitule_ec}"
    
    class Meta:
        db_table = 'elements_constitutifs'
        ordering = ['ue__code_ue', 'code_ec']
        constraints = [
            models.UniqueConstraint(
                fields=['ue', 'code_ec'],
                name='unique_ec_in_ue'
            )
        ]
        verbose_name = "Élément Constitutif"
        verbose_name_plural = "Éléments Constitutifs"

class SessionExamen(models.Model):
    TYPES_SESSION = [
        ('N', 'Session normale'),
        ('R', 'Session de rattrapage')
    ]

    id_session = models.AutoField(
        db_column='id_session',
        primary_key=True,
        db_comment="Identifiant unique de la session"
    )
    code_session = models.CharField(
        db_column='code_session',
        max_length=15,
        unique=True,
        db_comment="Code généré"
    )
    type_session = models.CharField(
        db_column='type_session',
        max_length=1,
        choices=TYPES_SESSION,
        db_comment="Type de session d'examen"
    )
    date_debut = models.DateField(
        db_column='date_debut',
        db_comment="Date d'ouverture de la session"
    )
    date_fin = models.DateField(
        db_column='date_fin',
        db_comment="Date de clôture de la session"
    )
    annee_universitaire = models.CharField(
        db_column='annee_universitaire',
        max_length=9,
        validators=[RegexValidator(r'^\d{4}-\d{4}$')],
        db_comment="Année universitaire"
    )

    def save(self, *args, **kwargs):
        if not self.code_session:
            self.code_session = f"{self.annee_universitaire[:4]}-S{self.type_session}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_session_display()} {self.annee_universitaire}"
    
    class Meta:
        db_table = 'sessions_examen'
        ordering = ['-annee_universitaire', 'type_session']
        indexes = [
            models.Index(fields=['date_debut', 'date_fin']),
            models.Index(fields=['type_session'])
        ]
        verbose_name = "Session d'examen"
        verbose_name_plural = "Sessions d'examen"    

class Note(models.Model):
    id_note = models.AutoField(
        db_column='id_note',
        primary_key=True,
        db_comment="Identifiant unique de la note"
    )
    etudiant = models.ForeignKey(
        Etudiant,
        db_column='id_etudiant',
        on_delete=models.CASCADE,
        related_name='notes',
        db_comment="Étudiant concerné"
    )
    ec = models.ForeignKey(
        EC,
        db_column='id_ec',
        on_delete=models.PROTECT,
        related_name='notes',
        db_comment="Élément constitutif"
    )
    session = models.ForeignKey(
        SessionExamen,
        db_column='id_session',
        on_delete=models.PROTECT,
        related_name='notes',
        db_comment="Session d'examen"
    )
    valeur = models.FloatField(
        db_column='valeur_note',
        validators=[MinValueValidator(0.0), MaxValueValidator(20.0)],
        db_comment="Note finale sur 20"
    )
    date_validation = models.DateTimeField(
        db_column='date_validation',
        auto_now_add=True,
        db_comment="Date de l'enregistrement"
    )

    def __str__(self):
        return f"{self.etudiant.matricule} | {self.ec.code_ec} | {self.valeur}/20"

    class Meta:
        db_table = 'notes'
        unique_together = ('etudiant', 'ec', 'session')
        indexes = [
            models.Index(fields=['valeur']),
            models.Index(fields=['date_validation'])
        ]
        verbose_name = "Note académique"
        verbose_name_plural = "Notes académiques"
