# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestSecurityAccess(TransactionCase):
    """Test security constraints protecting quiz and flashcard questions/answers from learners."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Node = cls.env['kms.node']
        Question = cls.env['kms.quiz.question']
        Answer = cls.env['kms.quiz.answer']
        Flashcard = cls.env['kms.flashcard']
        Course = cls.env['kms.course']
        UserNode = cls.env['kms.user.node']

        # Create learner user with group_kms_learner
        cls.learner_group = cls.env.ref('kms_mastery.group_kms_learner')
        cls.instructor_group = cls.env.ref('kms_mastery.group_kms_instructor')

        cls.learner = cls.env['res.users'].create({
            'name': 'Test Security Learner',
            'login': 'test_sec_learner',
            'group_ids': [(6, 0, [cls.learner_group.id, cls.env.ref('base.group_user').id])],
        })

        cls.instructor = cls.env['res.users'].create({
            'name': 'Test Security Instructor',
            'login': 'test_sec_instructor',
            'group_ids': [(6, 0, [cls.instructor_group.id, cls.env.ref('base.group_user').id])],
        })

        # Create Nodes: Root (A) -> Dependent (B)
        cls.node_a = Node.create({
            'name': 'Node A (Unlocked)',
            'description': '<p>Learn Node A concepts here.</p>',
            'resource_url': 'https://example.com/a',
            'mastery_threshold': 0.8,
        })
        cls.node_b = Node.create({
            'name': 'Node B (Locked)',
            'description': '<p>Learn Node B concepts here.</p>',
            'mastery_threshold': 0.8,
            'prerequisite_ids': [(4, cls.node_a.id)],
        })

        # Questions & Answers on Node A
        cls.q_a = Question.create({
            'node_id': cls.node_a.id,
            'question_text': '<p>Node A Question</p>',
            'type': 'mcq',
        })
        cls.a_a_correct = Answer.create({
            'question_id': cls.q_a.id,
            'text': 'Correct A',
            'is_correct': True,
        })
        cls.a_a_wrong = Answer.create({
            'question_id': cls.q_a.id,
            'text': 'Wrong A',
            'is_correct': False,
        })

        # Flashcards on Node A
        cls.fc_a = Flashcard.create({
            'node_id': cls.node_a.id,
            'front': '<p>Front A</p>',
            'back': '<p>Back A (Secret Answer)</p>',
        })

        # Questions & Answers on Node B
        cls.q_b = Question.create({
            'node_id': cls.node_b.id,
            'question_text': '<p>Node B Question</p>',
            'type': 'mcq',
        })
        cls.a_b_correct = Answer.create({
            'question_id': cls.q_b.id,
            'text': 'Correct B',
            'is_correct': True,
        })

        # Flashcards on Node B
        cls.fc_b = Flashcard.create({
            'node_id': cls.node_b.id,
            'front': '<p>Front B</p>',
            'back': '<p>Back B</p>',
        })

        # Create Course and enroll learner
        cls.course = Course.create({
            'name': 'Mastery Course',
            'node_ids': [(6, 0, [cls.node_a.id, cls.node_b.id])],
            'learner_ids': [(4, cls.learner.id)],
        })

        # Create user node progress records
        cls.un_a = UserNode.create({
            'user_id': cls.learner.id,
            'node_id': cls.node_a.id,
            'state': 'unlocked',
        })
        cls.un_b = UserNode.create({
            'user_id': cls.learner.id,
            'node_id': cls.node_b.id,
            'state': 'locked',
        })

    def test_learner_cannot_read_is_correct_field(self):
        """Learner must not have access to the is_correct field on kms.quiz.answer."""
        AnswerLearner = self.env['kms.quiz.answer'].with_user(self.learner)
        # Attempting to read is_correct field as learner should raise an AccessError or omit it
        ans = AnswerLearner.browse(self.a_a_correct.id)
        with self.assertRaises(AccessError):
            _ = ans.is_correct

    def test_instructor_can_read_is_correct_field(self):
        """Instructor must have access to the is_correct field on kms.quiz.answer."""
        AnswerInstructor = self.env['kms.quiz.answer'].with_user(self.instructor)
        ans = AnswerInstructor.browse(self.a_a_correct.id)
        self.assertTrue(ans.is_correct)

    def test_learner_can_access_learning_content(self):
        """Learner must be able to read node description, URLs, prerequisites."""
        NodeLearner = self.env['kms.node'].with_user(self.learner)
        node = NodeLearner.browse(self.node_a.id)
        self.assertEqual(node.name, 'Node A (Unlocked)')
        self.assertIn('Learn Node A concepts here.', node.description)
        self.assertEqual(node.resource_url, 'https://example.com/a')

    def test_learner_cannot_read_unmastered_flashcards(self):
        """Learner cannot read flashcard records for nodes they haven't mastered."""
        FlashcardLearner = self.env['kms.flashcard'].with_user(self.learner)
        # Node A is unlocked but not mastered -> no user_flashcard record yet
        found = FlashcardLearner.search([('id', '=', self.fc_a.id)])
        self.assertFalse(found, "Learner should not be able to find unmastered flashcards.")

        # Node B is locked -> learner should not see fc_b
        found_b = FlashcardLearner.search([('id', '=', self.fc_b.id)])
        self.assertFalse(found_b, "Learner should not see flashcards of locked nodes.")

    def test_learner_can_review_flashcards_after_mastery(self):
        """After mastering a node, learner can read flashcard content via kms.user.flashcard."""
        # Master Node A
        self.un_a.action_submit_quiz([
            {'question_id': self.q_a.id, 'answer_id': self.a_a_correct.id},
        ])
        self.assertEqual(self.un_a.state, 'mastered')

        # Now learner can access fc_a
        FlashcardLearner = self.env['kms.flashcard'].with_user(self.learner)
        found = FlashcardLearner.search([('id', '=', self.fc_a.id)])
        self.assertEqual(len(found), 1)

        # Learner reviews via kms.user.flashcard
        UserFcLearner = self.env['kms.user.flashcard'].with_user(self.learner)
        ufc = UserFcLearner.search([('flashcard_id', '=', self.fc_a.id), ('user_id', '=', self.learner.id)], limit=1)
        self.assertTrue(ufc)
        self.assertIn('Front A', ufc.front)
        self.assertIn('Back A (Secret Answer)', ufc.back)

    def test_learner_cannot_access_locked_node_questions(self):
        """Learner cannot access quiz questions or answers for locked nodes."""
        QuestionLearner = self.env['kms.quiz.question'].with_user(self.learner)
        AnswerLearner = self.env['kms.quiz.answer'].with_user(self.learner)

        # Questions for Node B (locked) must not be accessible to learner
        found_q = QuestionLearner.search([('id', '=', self.q_b.id)])
        self.assertFalse(found_q, "Learner should not be able to find quiz questions of locked nodes.")

        found_a = AnswerLearner.search([('id', '=', self.a_b_correct.id)])
        self.assertFalse(found_a, "Learner should not be able to find quiz answers of locked nodes.")

    def test_learner_can_access_unlocked_node_questions_in_wizard(self):
        """Learner can load questions and answer options for unlocked node in the quiz wizard."""
        QuestionLearner = self.env['kms.quiz.question'].with_user(self.learner)
        AnswerLearner = self.env['kms.quiz.answer'].with_user(self.learner)

        # Node A is unlocked
        found_q = QuestionLearner.search([('id', '=', self.q_a.id)])
        self.assertEqual(len(found_q), 1)

        found_a = AnswerLearner.search([('question_id', '=', self.q_a.id)])
        self.assertEqual(len(found_a), 2)
        # Verify answer texts are available (e.g. for dropdown choices)
        texts = {a.text for a in found_a}
        self.assertEqual(texts, {'Correct A', 'Wrong A'})

    def test_quiz_wizard_flow_for_learner(self):
        """Quiz wizard works end-to-end for learner without leaking is_correct."""
        Wizard = self.env['kms.quiz.wizard'].with_user(self.learner)
        defaults = Wizard.with_context(default_user_node_id=self.un_a.id).default_get([
            'user_node_id', 'line_ids'
        ])
        wizard = Wizard.create({
            'user_node_id': self.un_a.id,
            'line_ids': [
                (0, 0, {
                    'question_id': self.q_a.id,
                    'selected_answer_id': self.a_a_correct.id,
                })
            ],
        })
        res = wizard.action_submit()
        self.assertEqual(res['params']['type'], 'success')
        self.assertEqual(self.un_a.state, 'mastered')
