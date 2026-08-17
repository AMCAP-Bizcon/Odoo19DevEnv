# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class KmsMilestone(models.Model):
    """Human-graded assignment tied to a set of nodes within a course."""

    _name = 'kms.milestone'
    _description = 'KMS Milestone'
    _order = 'sequence, id'

    name = fields.Char(string='Milestone Name', required=True)
    description = fields.Html(string='Assignment Instructions')
    course_id = fields.Many2one(
        'kms.course',
        string='Course',
        required=True,
        ondelete='cascade',
    )
    instructor_id = fields.Many2one(
        'res.users',
        string='Grading Instructor',
        help='Defaults to the course instructor if left blank.',
    )
    node_ids = fields.Many2many(
        'kms.node',
        'kms_milestone_node_rel',
        'milestone_id',
        'node_id',
        string='Assessed Nodes',
    )
    sequence = fields.Integer(default=10)

    def _get_instructor(self):
        """Return the effective instructor for this milestone."""
        self.ensure_one()
        return self.instructor_id or self.course_id.instructor_id
