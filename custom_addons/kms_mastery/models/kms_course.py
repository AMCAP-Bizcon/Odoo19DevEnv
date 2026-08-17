# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class KmsCourse(models.Model):
    """Enrollment scope: groups nodes into learnable courses."""

    _name = 'kms.course'
    _description = 'KMS Course'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

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

    def action_enroll_learner(self, user):
        """Enroll a user in this course and initialise their node progress."""
        self.ensure_one()
        self.write({'learner_ids': [(4, user.id)]})
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
