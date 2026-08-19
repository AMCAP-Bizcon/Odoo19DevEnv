# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class KmsCourse(models.Model):
    """Enrollment scope: groups nodes into learnable courses."""

    _name = 'kms.course'
    _description = 'KMS Course'
    _inherit = ['mail.thread']
    _order = 'sequence, id'
    _rec_name = 'name'

    name = fields.Char(string='Course Name', required=True, tracking=True)
    description = fields.Html(string='Course Overview')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    instructor_id = fields.Many2one(
        'res.users',
        string='Primary Instructor',
        domain=lambda self: [('group_ids', 'in', self.env.ref('kms_mastery.group_kms_instructor').id)],
        tracking=True,
    )

    node_ids = fields.Many2many(
        'kms.node',
        'kms_course_node_rel',
        'course_id',
        'node_id',
        string='Knowledge Nodes',
    )
    milestone_ids = fields.One2many(
        'kms.milestone',
        'course_id',
        string='Milestones',
    )
    learner_ids = fields.Many2many(
        'res.users',
        'kms_course_learner_rel',
        'course_id',
        'user_id',
        string='Enrolled Learners',
    )

    # Computed fields
    node_count = fields.Integer(
        string='Node Count',
        compute='_compute_node_count',
    )
    learner_count = fields.Integer(
        string='Learner Count',
        compute='_compute_learner_count',
    )

    @api.depends('node_ids')
    def _compute_node_count(self):
        for rec in self:
            rec.node_count = len(rec.node_ids)

    @api.depends('learner_ids')
    def _compute_learner_count(self):
        for rec in self:
            rec.learner_count = len(rec.learner_ids)

    def action_view_nodes(self):
        """Open the list or form view of nodes associated with this course."""
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('kms_mastery.kms_node_action')
        action['domain'] = [('id', 'in', self.node_ids.ids)]
        action['context'] = {
            'default_course_ids': [(4, self.id)],
        }
        if len(self.node_ids) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.node_ids.id
        return action

    def _init_learner_progress(self, user):
        """Initialise node progress and check milestones for a specific user in this course."""
        self.ensure_one()
        UserNode = self.env['kms.user.node']
        for node in self.node_ids:
            existing = UserNode.search([
                ('user_id', '=', user.id),
                ('node_id', '=', node.id),
            ], limit=1)
            if not existing:
                # Determine initial state: unlocked if no prerequisites
                state = 'unlocked' if not node.prerequisite_ids else 'locked'
                UserNode.create({
                    'user_id': user.id,
                    'node_id': node.id,
                    'state': state,
                })

        # Check and assign any course milestones whose nodes are already mastered
        UserMilestone = self.env['kms.user.milestone'].sudo()
        for milestone in self.milestone_ids:
            if not milestone.node_ids:
                continue
            mastered_count = UserNode.sudo().search_count([
                ('user_id', '=', user.id),
                ('node_id', 'in', milestone.node_ids.ids),
                ('state', '=', 'mastered'),
            ])
            if mastered_count == len(milestone.node_ids):
                existing = UserMilestone.search([
                    ('user_id', '=', user.id),
                    ('milestone_id', '=', milestone.id),
                ], limit=1)
                if not existing:
                    UserMilestone.create({
                        'user_id': user.id,
                        'milestone_id': milestone.id,
                        'state': 'pending',
                    })

    def action_enroll_learner(self, user):
        """Enroll a user in this course and initialise their node progress."""
        self.ensure_one()
        self.write({'learner_ids': [(4, user.id)]})
        self._init_learner_progress(user)

    @api.model_create_multi
    def create(self, vals_list):
        courses = super().create(vals_list)
        for course in courses:
            for user in course.learner_ids:
                course._init_learner_progress(user)
        return courses

    def write(self, vals):
        if 'learner_ids' in vals:
            old_learners = {course.id: set(course.learner_ids.ids) for course in self}
        
        res = super().write(vals)
        
        if 'learner_ids' in vals:
            for course in self:
                current_learners = set(course.learner_ids.ids)
                new_learner_ids = current_learners - old_learners[course.id]
                for user_id in new_learner_ids:
                    user = self.env['res.users'].browse(user_id)
                    course._init_learner_progress(user)
                    
        return res

