# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class KmsQuizAnswer(models.Model):
    """An answer option for a quiz question."""

    _name = 'kms.quiz.answer'
    _description = 'KMS Quiz Answer'
    _order = 'sequence, id'

    question_id = fields.Many2one(
        'kms.quiz.question',
        string='Question',
        required=True,
        ondelete='cascade',
    )
    text = fields.Char(string='Answer Text', required=True)
    is_correct = fields.Boolean(string='Correct Answer', default=False)
    sequence = fields.Integer(default=10)
