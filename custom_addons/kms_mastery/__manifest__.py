{
    'name': 'KMS Mastery Learning',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'author': 'Antigravity',
    'summary': 'Mastery-based Knowledge Management with DAG, Quizzes, FSRS Flashcards, and Milestones',
    'description': """
Mastery Learning Knowledge Management System
=============================================
- Directed Acyclic Graph (DAG) of knowledge nodes with prerequisite enforcement
- Auto-graded quizzes with configurable mastery thresholds
- Modern FSRS spaced-repetition flashcards for long-term retention
- Human-graded milestone assignments with daily reminder notifications
- Interactive OWL DAG visualization component
    """,
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        # Security (must load first)
        'security/kms_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        # Views (ordered by action dependency)
        'wizard/kms_quiz_wizard_views.xml',
        'views/kms_quiz_views.xml',
        'views/kms_flashcard_views.xml',
        'views/kms_milestone_views.xml',
        'views/kms_learner_views.xml',
        'views/kms_course_views.xml',
        'views/kms_node_views.xml',
        'views/kms_menus.xml',
    ],
    'demo': [
        'demo/kms_demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kms_mastery/static/src/**/*',
            ('remove', 'kms_mastery/static/src/**/*.dark.scss'),
        ],
        'web.assets_web_dark': [
            'kms_mastery/static/src/**/*.dark.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
