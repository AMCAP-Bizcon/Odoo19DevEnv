# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class KmsQuizQuestion(models.Model):
    """A quiz question belonging to a knowledge node."""

    _name = 'kms.quiz.question'
    _description = 'KMS Quiz Question'
    _order = 'sequence, id'

    node_id = fields.Many2one(
        'kms.node',
        string='Knowledge Node',
        required=True,
        ondelete='cascade',
    )
    question_text = fields.Html(string='Question', required=True)
    type = fields.Selection(
        [
            ('mcq', 'Multiple Choice'),
            ('tf', 'True/False'),
        ],
        string='Question Type',
        default='mcq',
        required=True,
    )
    answer_ids = fields.One2many(
        'kms.quiz.answer',
        'question_id',
        string='Answer Options',
    )
    sequence = fields.Integer(default=10)
