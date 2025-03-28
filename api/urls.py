"""
URL configuration for backend_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .views import UserInfoView, UpdateUserInfoView, PhotoUpdateView, RolesListView
from . import views

urlpatterns = [
    path('user-info/', UserInfoView.as_view(), name='user_info'),
    path('user-info/update/<int:_idUtilisateur>', UpdateUserInfoView.as_view(), name='update_user_info'),
    path('user-info/update-photo/', PhotoUpdateView.as_view(), name='upload_profile_image'),
    path('user-info/roles/', RolesListView.as_view(), name='liste_roles'),

    path('utilisateur/', views.manage_utilisateur, name='crud_utilisateur'),
    path('utilisateur/<int:_id_utilisateur>/', views.manage_utilisateur, name='crud_utilisateur'),
    
    path('etudiant/', views.manage_etudiant, name='crud_etudiant'),
    path('etudiant/<int:_id_etudiant>/', views.manage_etudiant, name='crud_etudiant'),

    path('enseignant/', views.manage_enseignant, name='crud_enseignant'),
    path('enseignant/<int:_id_enseignant>/', views.manage_enseignant, name='crud_enseignant'),
    
    path('classe/', views.manage_classe, name='crud_classe'),
    path('classe/<int:_id_classe>/', views.manage_classe, name='crud_classe'),
    
    path('inscription/', views.manage_inscription, name='crud_inscription'),
    path('inscription/<int:_id_inscription>/', views.manage_inscription, name='crud_inscription'),
    
    path('session/', views.manage_session, name='crud_session'),
    path('session/<int:_id_session>/', views.manage_session, name='crud_session'),
    
    path('ue/', views.manage_ue, name='crud_ue'),
    path('ue/<int:_id_ue>/', views.manage_ue, name='crud_ue'),

    path('ec/', views.manage_ec, name='crud_ec'),
    path('ec/<int:_id_ec>/', views.manage_ec, name='crud_ec'),
    
    path('note/', views.manage_note, name='crud_note'),
    path('note/<int:_id_note>/', views.manage_note, name='crud_note'),
    
    path('etudiants/classe/<int:id_classe>/annee/<str:annee_academique>/', 
         views.get_etudiants_by_classe_annee, name='etudiants_by_classe_annee'),
    path('etudiant/<int:id_etudiant>/notes/', 
         views.get_notes_by_etudiant, name='notes_by_etudiant'),

]

