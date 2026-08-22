# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

# pyrefly: ignore [missing-import]
from odoo.tests.common import TransactionCase


class TestMenuNavigation(TransactionCase):
    """Test feature-based menu reorganization and associated actions."""

    def test_top_level_menus_exist(self):
        """Verify the three top-level menus exist under the root menu."""
        root_menu = self.env.ref('kms_mastery.kms_root_menu')
        self.assertTrue(root_menu)

        courses_menu = self.env.ref('kms_mastery.kms_courses_menu')
        self.assertTrue(courses_menu)
        self.assertEqual(courses_menu.parent_id.id, root_menu.id)

        dag_menu = self.env.ref('kms_mastery.kms_dag_menu')
        self.assertTrue(dag_menu)
        self.assertEqual(dag_menu.parent_id.id, root_menu.id)

        reports_menu = self.env.ref('kms_mastery.kms_reports_menu')
        self.assertTrue(reports_menu)
        self.assertEqual(reports_menu.parent_id.id, root_menu.id)

    def test_courses_submenus_and_actions(self):
        """Verify Courses submenus: My Courses and All Courses."""
        courses_menu = self.env.ref('kms_mastery.kms_courses_menu')

        my_courses_menu = self.env.ref('kms_mastery.kms_my_courses_menu')
        self.assertTrue(my_courses_menu)
        self.assertEqual(my_courses_menu.parent_id.id, courses_menu.id)
        self.assertEqual(my_courses_menu.action.res_model, 'kms.course')

        all_courses_menu = self.env.ref('kms_mastery.kms_all_courses_menu')
        self.assertTrue(all_courses_menu)
        self.assertEqual(all_courses_menu.parent_id.id, courses_menu.id)
        self.assertEqual(all_courses_menu.action.res_model, 'kms.course')

        # Check My Courses action domain includes both learner and instructor
        my_course_action = self.env.ref('kms_mastery.kms_my_course_action')
        self.assertIn('learner_ids', str(my_course_action.domain))
        self.assertIn('instructor_id', str(my_course_action.domain))

    def test_knowledge_graph_submenus_and_actions(self):
        """Verify Knowledge Graph submenus: My Graph and Full Graph."""
        dag_menu = self.env.ref('kms_mastery.kms_dag_menu')

        my_dag_menu = self.env.ref('kms_mastery.kms_my_dag_menu')
        self.assertTrue(my_dag_menu)
        self.assertEqual(my_dag_menu.parent_id.id, dag_menu.id)

        full_dag_menu = self.env.ref('kms_mastery.kms_full_dag_menu')
        self.assertTrue(full_dag_menu)
        self.assertEqual(full_dag_menu.parent_id.id, dag_menu.id)

        # Check client actions
        full_action = self.env.ref('kms_mastery.kms_dag_viewer_action')
        self.assertEqual(full_action.tag, 'kms_mastery.dag_viewer')

        my_action = self.env.ref('kms_mastery.kms_my_dag_viewer_action')
        self.assertEqual(my_action.tag, 'kms_mastery.dag_viewer')
        self.assertIn('my_nodes_only', str(my_action.params) + str(my_action.context))

    def test_performance_reports_submenus_and_actions(self):
        """Verify Performance Reports submenus: Learning Progress, Quiz Attempts, Milestone Submissions, Flashcard Reviews."""
        reports_menu = self.env.ref('kms_mastery.kms_reports_menu')

        learning_progress_menu = self.env.ref('kms_mastery.kms_user_node_report_menu')
        self.assertTrue(learning_progress_menu)
        self.assertEqual(learning_progress_menu.parent_id.id, reports_menu.id)
        self.assertEqual(learning_progress_menu.action.res_model, 'kms.user.node')

        quiz_menu = self.env.ref('kms_mastery.kms_quiz_attempts_menu')
        self.assertTrue(quiz_menu)
        self.assertEqual(quiz_menu.parent_id.id, reports_menu.id)
        self.assertEqual(quiz_menu.action.res_model, 'kms.quiz.attempt')

        milestone_menu = self.env.ref('kms_mastery.kms_milestone_submissions_menu')
        self.assertTrue(milestone_menu)
        self.assertEqual(milestone_menu.parent_id.id, reports_menu.id)
        self.assertEqual(milestone_menu.action.res_model, 'kms.user.milestone')

        flashcard_report_menu = self.env.ref('kms_mastery.kms_user_flashcard_report_menu')
        self.assertTrue(flashcard_report_menu)
        self.assertEqual(flashcard_report_menu.parent_id.id, reports_menu.id)
        self.assertEqual(flashcard_report_menu.action.res_model, 'kms.user.flashcard')

    def test_user_flashcard_node_id_relation(self):
        """Verify that kms.user.flashcard correctly relates to its knowledge node."""
        node = self.env['kms.node'].create({'name': 'Test Flashcard Node'})
        flashcard = self.env['kms.flashcard'].create({
            'node_id': node.id,
            'front': '<p>Front</p>',
            'back': '<p>Back</p>',
        })
        user = self.env['res.users'].create({
            'name': 'Test FC User',
            'login': 'test_fc_user',
            'group_ids': [(6, 0, [self.env.ref('kms_mastery.group_kms_learner').id, self.env.ref('base.group_user').id])],
        })
        user_fc = self.env['kms.user.flashcard'].create({
            'user_id': user.id,
            'flashcard_id': flashcard.id,
        })
        self.assertEqual(user_fc.node_id.id, node.id)

    def test_course_instructor_milestone_action_and_count(self):
        """Verify course milestone_count computation and action_view_milestones method."""
        course = self.env['kms.course'].create({'name': 'Test Milestone Course'})
        self.assertEqual(course.milestone_count, 0)

        ms = self.env['kms.milestone'].create({
            'name': 'Project 1',
            'course_id': course.id,
        })
        self.assertEqual(course.milestone_count, 1)

        action = course.action_view_milestones()
        self.assertEqual(action['res_id'], ms.id)
        self.assertIn(('course_id', '=', course.id), action['domain'])

    def test_role_visibility_flags(self):
        """Verify is_instructor computed field distinguishes instructors from learners."""
        learner_group = self.env.ref('kms_mastery.group_kms_learner')
        instructor_group = self.env.ref('kms_mastery.group_kms_instructor')

        learner = self.env['res.users'].create({
            'name': 'Test Vis Learner',
            'login': 'test_vis_learner',
            'group_ids': [(6, 0, [learner_group.id, self.env.ref('base.group_user').id])],
        })
        instructor = self.env['res.users'].create({
            'name': 'Test Vis Instructor',
            'login': 'test_vis_instructor',
            'group_ids': [(6, 0, [instructor_group.id, self.env.ref('base.group_user').id])],
        })

        course = self.env['kms.course'].create({'name': 'Course Vis'})
        node = self.env['kms.node'].create({'name': 'Node Vis'})

        self.assertFalse(course.with_user(learner).is_instructor)
        self.assertTrue(course.with_user(instructor).is_instructor)

        self.assertFalse(node.with_user(learner).is_instructor)
        self.assertTrue(node.with_user(instructor).is_instructor)
