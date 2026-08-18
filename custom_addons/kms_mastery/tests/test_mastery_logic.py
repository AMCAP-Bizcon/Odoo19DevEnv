# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

# pyrefly: ignore [missing-import]
from odoo.tests.common import TransactionCase


class TestMasteryLogic(TransactionCase):
    """Test mastery state transitions, quiz submission, and flashcard auto-creation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Node = cls.env['kms.node']
        Question = cls.env['kms.quiz.question']
        Answer = cls.env['kms.quiz.answer']
        Flashcard = cls.env['kms.flashcard']
        UserNode = cls.env['kms.user.node']

        # Create a learner user with group_kms_learner
        learner_group = cls.env.ref('kms_mastery.group_kms_learner')
        cls.learner = cls.env['res.users'].create({
            'name': 'Test Learner',
            'login': 'test_learner_mastery',
            'password': 'test_learner_mastery',
            'group_ids': [(6, 0, [learner_group.id, cls.env.ref('base.group_user').id])],
        })

        # Create nodes: A → B
        cls.node_a = Node.create({
            'name': 'Test Node A',
            'mastery_threshold': 0.5,  # 50% to pass (easier for tests)
        })
        cls.node_b = Node.create({
            'name': 'Test Node B',
            'mastery_threshold': 0.5,
            'prerequisite_ids': [(4, cls.node_a.id)],
        })

        # Create quiz questions for Node A
        cls.q1 = Question.create({
            'node_id': cls.node_a.id,
            'question_text': '<p>Question 1</p>',
            'type': 'mcq',
        })
        cls.q1_correct = Answer.create({
            'question_id': cls.q1.id,
            'text': 'Correct Answer',
            'is_correct': True,
        })
        cls.q1_wrong = Answer.create({
            'question_id': cls.q1.id,
            'text': 'Wrong Answer',
            'is_correct': False,
        })

        cls.q2 = Question.create({
            'node_id': cls.node_a.id,
            'question_text': '<p>Question 2</p>',
            'type': 'tf',
        })
        cls.q2_correct = Answer.create({
            'question_id': cls.q2.id,
            'text': 'True',
            'is_correct': True,
        })
        cls.q2_wrong = Answer.create({
            'question_id': cls.q2.id,
            'text': 'False',
            'is_correct': False,
        })

        # Create flashcards for Node A
        cls.fc1 = Flashcard.create({
            'node_id': cls.node_a.id,
            'front': '<p>Front 1</p>',
            'back': '<p>Back 1</p>',
        })
        cls.fc2 = Flashcard.create({
            'node_id': cls.node_a.id,
            'front': '<p>Front 2</p>',
            'back': '<p>Back 2</p>',
        })

        # Create user-node progress records
        cls.un_a = UserNode.with_user(cls.learner).create({
            'user_id': cls.learner.id,
            'node_id': cls.node_a.id,
            'state': 'unlocked',
        })
        cls.un_b = UserNode.with_user(cls.learner).create({
            'user_id': cls.learner.id,
            'node_id': cls.node_b.id,
            'state': 'locked',
        })

    def test_initial_state(self):
        """Node B should start as locked since it requires A."""
        self.assertEqual(self.un_b.state, 'locked')

    def test_failing_quiz_keeps_unlocked(self):
        """Submitting a failing quiz should keep node A as unlocked."""
        # Answer both questions wrong = 0% score < 50% threshold
        self.un_a.action_submit_quiz([
            {'question_id': self.q1.id, 'answer_id': self.q1_wrong.id},
            {'question_id': self.q2.id, 'answer_id': self.q2_wrong.id},
        ])
        self.assertEqual(self.un_a.state, 'unlocked')

    def test_passing_quiz_masters_node(self):
        """Submitting a passing quiz should master node A."""
        # Answer both correctly = 100% score >= 50% threshold
        self.un_a.action_submit_quiz([
            {'question_id': self.q1.id, 'answer_id': self.q1_correct.id},
            {'question_id': self.q2.id, 'answer_id': self.q2_correct.id},
        ])
        self.assertEqual(self.un_a.state, 'mastered')
        self.assertTrue(self.un_a.mastered_date)

    def test_passing_quiz_unlocks_dependent(self):
        """Mastering node A should unlock node B."""
        self.un_a.action_submit_quiz([
            {'question_id': self.q1.id, 'answer_id': self.q1_correct.id},
            {'question_id': self.q2.id, 'answer_id': self.q2_correct.id},
        ])
        # Refresh node B
        self.un_b.invalidate_recordset()
        self.assertEqual(self.un_b.state, 'unlocked')

    def test_flashcards_auto_created(self):
        """Mastering a node should auto-create user flashcard records."""
        self.un_a.action_submit_quiz([
            {'question_id': self.q1.id, 'answer_id': self.q1_correct.id},
            {'question_id': self.q2.id, 'answer_id': self.q2_correct.id},
        ])
        user_flashcards = self.env['kms.user.flashcard'].search([
            ('user_id', '=', self.learner.id),
            ('flashcard_id', 'in', [self.fc1.id, self.fc2.id]),
        ])
        self.assertEqual(len(user_flashcards), 2)

    def test_quiz_attempt_recorded(self):
        """Each quiz submission should create a quiz attempt record."""
        self.un_a.action_submit_quiz([
            {'question_id': self.q1.id, 'answer_id': self.q1_correct.id},
            {'question_id': self.q2.id, 'answer_id': self.q2_wrong.id},
        ])
        attempts = self.env['kms.quiz.attempt'].search([
            ('user_id', '=', self.learner.id),
            ('node_id', '=', self.node_a.id),
        ])
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].score, 0.5)  # 1/2 correct

    def test_best_score_updated(self):
        """Best quiz score should be updated after each attempt."""
        # First attempt: 50%
        self.un_a.action_submit_quiz([
            {'question_id': self.q1.id, 'answer_id': self.q1_correct.id},
            {'question_id': self.q2.id, 'answer_id': self.q2_wrong.id},
        ])
        self.assertEqual(self.un_a.best_quiz_score, 0.5)

        # Second attempt: 100%
        self.un_a.action_submit_quiz([
            {'question_id': self.q1.id, 'answer_id': self.q1_correct.id},
            {'question_id': self.q2.id, 'answer_id': self.q2_correct.id},
        ])
        self.assertEqual(self.un_a.best_quiz_score, 1.0)
