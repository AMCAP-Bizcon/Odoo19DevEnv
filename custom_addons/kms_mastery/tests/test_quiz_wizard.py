# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestQuizWizard(TransactionCase):
    """Test the KMS Quiz Wizard interaction and grading flow."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Node = cls.env['kms.node']
        Question = cls.env['kms.quiz.question']
        Answer = cls.env['kms.quiz.answer']
        UserNode = cls.env['kms.user.node']

        # Create a learner user
        cls.learner = cls.env['res.users'].create({
            'name': 'Test Wizard Learner',
            'login': 'test_wizard_learner',
            'password': 'test_wizard_learner',
        })

        # Create knowledge node
        cls.node = Node.create({
            'name': 'Python Basics',
            'mastery_threshold': 0.7,
        })

        # Create Questions & Answers
        cls.q1 = Question.create({
            'node_id': cls.node.id,
            'question_text': '<p>Is Python interpreted?</p>',
            'type': 'tf',
        })
        cls.q1_yes = Answer.create({
            'question_id': cls.q1.id,
            'text': 'Yes',
            'is_correct': True,
        })
        cls.q1_no = Answer.create({
            'question_id': cls.q1.id,
            'text': 'No',
            'is_correct': False,
        })

        cls.q2 = Question.create({
            'node_id': cls.node.id,
            'question_text': '<p>What is 2 + 2?</p>',
            'type': 'mcq',
        })
        cls.q2_4 = Answer.create({
            'question_id': cls.q2.id,
            'text': '4',
            'is_correct': True,
        })
        cls.q2_5 = Answer.create({
            'question_id': cls.q2.id,
            'text': '5',
            'is_correct': False,
        })

        # User node record
        cls.user_node = UserNode.with_user(cls.learner).create({
            'user_id': cls.learner.id,
            'node_id': cls.node.id,
            'state': 'unlocked',
        })

    def test_wizard_default_get_populates_questions(self):
        """Wizard should populate line_ids with questions from the node."""
        Wizard = self.env['kms.quiz.wizard'].with_user(self.learner)
        defaults = Wizard.with_context(default_user_node_id=self.user_node.id).default_get([
            'user_node_id', 'line_ids'
        ])
        self.assertEqual(defaults.get('user_node_id'), self.user_node.id)
        lines = defaults.get('line_ids', [])
        self.assertEqual(len(lines), 2)
        question_ids = {line[2]['question_id'] for line in lines}
        self.assertEqual(question_ids, {self.q1.id, self.q2.id})

    def test_wizard_submit_unanswered_raises_error(self):
        """Submitting with unanswered questions must raise a UserError."""
        wizard = self.env['kms.quiz.wizard'].with_user(self.learner).create({
            'user_node_id': self.user_node.id,
            'line_ids': [
                (0, 0, {'question_id': self.q1.id}),
                (0, 0, {'question_id': self.q2.id}),
            ],
        })
        with self.assertRaises(UserError):
            wizard.action_submit()

    def test_wizard_submit_passing_flow(self):
        """Submitting passing answers through the wizard should master the node."""
        wizard = self.env['kms.quiz.wizard'].with_user(self.learner).create({
            'user_node_id': self.user_node.id,
            'line_ids': [
                (0, 0, {'question_id': self.q1.id, 'selected_answer_id': self.q1_yes.id}),
                (0, 0, {'question_id': self.q2.id, 'selected_answer_id': self.q2_4.id}),
            ],
        })
        res = wizard.action_submit()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(res['params']['type'], 'success')

        # Verify user node state
        self.assertEqual(self.user_node.state, 'mastered')
        self.assertEqual(self.user_node.best_quiz_score, 1.0)

    def test_wizard_submit_failing_flow(self):
        """Submitting failing answers should not master the node."""
        wizard = self.env['kms.quiz.wizard'].with_user(self.learner).create({
            'user_node_id': self.user_node.id,
            'line_ids': [
                (0, 0, {'question_id': self.q1.id, 'selected_answer_id': self.q1_no.id}),
                (0, 0, {'question_id': self.q2.id, 'selected_answer_id': self.q2_5.id}),
            ],
        })
        res = wizard.action_submit()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(res['params']['type'], 'warning')

        # Verify user node remains unlocked
        self.assertEqual(self.user_node.state, 'unlocked')
        self.assertEqual(self.user_node.best_quiz_score, 0.0)
