# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
# pyrefly: ignore [missing-import]
from odoo.tools import html2plaintext


class KmsQuizQuestion(models.Model):
    """A quiz question belonging to a knowledge node."""

    _name = 'kms.quiz.question'
    _description = 'KMS Quiz Question'
    _order = 'sequence, id'
    _rec_name = 'name'

    name = fields.Char(string='Question Summary', compute='_compute_name', store=True)
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

    @api.depends('question_text', 'node_id.name')
    def _compute_name(self):
        for rec in self:
            clean_text = html2plaintext(rec.question_text or '').strip()
            if clean_text:
                rec.name = (clean_text[:60] + '...') if len(clean_text) > 60 else clean_text
            elif rec.node_id:
                rec.name = f"{rec.node_id.name} Question"
            else:
                rec.name = f"Question #{rec.id or rec.sequence}"
