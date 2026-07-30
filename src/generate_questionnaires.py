import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from questionnaires.models import Questionnaire, Question
from users.models import User

def generate_default_questionnaires():
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("No superuser found. Creating a generic admin 'admin@co3data.local'...")
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@co3data.local',
            password='password123',
            first_name='System',
            last_name='Admin',
            role='admin'
            # Assuming region is nullable or not required for superusers based on core logic
        )
        print("Created superuser admin@co3data.local")

    # 1. Member Census Questionnaire for Excel Data
    census_q, created = Questionnaire.objects.get_or_create(
        title="Recensement Détaillé des Membres (Fichier Excel NAKEZA)",
        target_model='member',
        defaults={
            'description': "Questionnaire to standardise data collection based on the NAKEZA Excel structure. Captures groupement, village, and tree counts.",
            'created_by': admin_user,
            'is_active': True
        }
    )

    if created:
        print(f"Created Questionnaire: {census_q.title}")
        Question.objects.create(
            questionnaire=census_q,
            text="Territoire (Ex: Kabare)",
            question_type='text',
            is_required=True,
            order=1
        )
        Question.objects.create(
            questionnaire=census_q,
            text="Groupement (Ex: Luhihi)",
            question_type='text',
            is_required=True,
            order=2
        )
        Question.objects.create(
            questionnaire=census_q,
            text="Village (Ex: Izimero)",
            question_type='text',
            is_required=True,
            order=3
        )
        Question.objects.create(
            questionnaire=census_q,
            text="Nombre des pies (Taille L/Ha ou Arbres)",
            question_type='number',
            is_required=True,
            order=4
        )
    else:
        print(f"Questionnaire already exists: {census_q.title}")

    # 2. Cooperative Leadership Structure
    leadership_q, created = Questionnaire.objects.get_or_create(
        title="Structure de Leadership de la Coopérative",
        target_model='cooperative',
        defaults={
            'description': "Capture contact information for key board members of the cooperative as defined in the NAKEZA data sheet.",
            'created_by': admin_user,
            'is_active': True
        }
    )

    if created:
        print(f"Created Questionnaire: {leadership_q.title}")
        Question.objects.create(
            questionnaire=leadership_q,
            text="Nom du Président",
            question_type='text',
            is_required=True,
            order=1
        )
        Question.objects.create(
            questionnaire=leadership_q,
            text="Contact du Président (Numéro de téléphone)",
            question_type='text',
            is_required=False,
            order=2
        )
        Question.objects.create(
            questionnaire=leadership_q,
            text="Nom du Vice-Président",
            question_type='text',
            is_required=True,
            order=3
        )
        Question.objects.create(
            questionnaire=leadership_q,
            text="Contact du Vice-Président",
            question_type='text',
            is_required=False,
            order=4
        )
        Question.objects.create(
            questionnaire=leadership_q,
            text="Nom du Secrétaire",
            question_type='text',
            is_required=True,
            order=5
        )
        Question.objects.create(
            questionnaire=leadership_q,
            text="Contact du Secrétaire",
            question_type='text',
            is_required=False,
            order=6
        )

    else:
        print(f"Questionnaire already exists: {leadership_q.title}")


if __name__ == '__main__':
    generate_default_questionnaires()
    print("Default questionnaires generation complete.")
