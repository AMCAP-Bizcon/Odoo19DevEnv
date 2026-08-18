# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class KmsNode(models.Model):
    """Core knowledge concept node in the DAG."""

    _name = 'kms.node'
    _description = 'KMS Knowledge Node'
    _order = 'sequence, id'

    name = fields.Char(string='Node Name', required=True)
    description = fields.Html(string='Learning Content')
    resource_url = fields.Char(string='External Resource URL')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'kms_node_attachment_rel',
        'node_id',
        'attachment_id',
        string='Attachments',
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    mastery_threshold = fields.Float(
        string='Mastery Threshold',
        default=0.9,
        help='Minimum quiz score (0.0–1.0) required to master this node.',
    )

    # DAG relationships (self-referential Many2many)
    prerequisite_ids = fields.Many2many(
        'kms.node',
        'kms_node_prerequisite_rel',
        'node_id',
        'prerequisite_id',
        string='Prerequisites',
    )
    dependent_ids = fields.Many2many(
        'kms.node',
        'kms_node_prerequisite_rel',
        'prerequisite_id',
        'node_id',
        string='Dependents',
    )

    # User Progress relationship
    user_node_ids = fields.One2many(
        'kms.user.node',
        'node_id',
        string='User Progress',
    )

    # Content relationships
    quiz_question_ids = fields.One2many(
        'kms.quiz.question',
        'node_id',
        string='Quiz Questions',
        groups='kms_mastery.group_kms_instructor',
    )
    flashcard_ids = fields.One2many(
        'kms.flashcard',
        'node_id',
        string='Flashcards',
        groups='kms_mastery.group_kms_instructor',
    )

    # Computed counts
    quiz_question_count = fields.Integer(
        string='Question Count',
        compute='_compute_quiz_question_count',
    )
    flashcard_count = fields.Integer(
        string='Flashcard Count',
        compute='_compute_flashcard_count',
    )

    @api.depends('quiz_question_ids')
    def _compute_quiz_question_count(self):
        for rec in self:
            rec.quiz_question_count = len(rec.sudo().quiz_question_ids)

    @api.depends('flashcard_ids')
    def _compute_flashcard_count(self):
        for rec in self:
            rec.flashcard_count = len(rec.sudo().flashcard_ids)

    @api.constrains('prerequisite_ids')
    def _check_no_cyclic_dependencies(self):
        """Ensure the prerequisite graph remains a DAG (no cycles)."""
        if self._has_cycle('prerequisite_ids'):
            raise ValidationError(
                _("Circular prerequisite dependency detected.")
            )
