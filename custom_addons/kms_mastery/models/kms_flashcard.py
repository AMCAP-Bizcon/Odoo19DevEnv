# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
# pyrefly: ignore [missing-import]
from odoo.tools import html2plaintext


class KmsFlashcard(models.Model):
    """A flashcard belonging to a knowledge node for spaced repetition."""

    _name = 'kms.flashcard'
    _description = 'KMS Flashcard'
    _order = 'sequence, id'
    _rec_name = 'name'

    name = fields.Char(string='Summary', compute='_compute_name', store=True)
    node_id = fields.Many2one(
        'kms.node',
        string='Knowledge Node',
        required=True,
        ondelete='cascade',
    )
    front = fields.Html(string='Front (Question)')
    back = fields.Html(string='Back (Answer)')
    sequence = fields.Integer(default=10)
    user_flashcard_ids = fields.One2many(
        'kms.user.flashcard',
        'flashcard_id',
        string='User Flashcards',
    )

    @api.depends('front', 'node_id.name', 'sequence')
    def _compute_name(self):
        for rec in self:
            clean_front = html2plaintext(rec.front or '').strip()
            if clean_front:
                truncated = (clean_front[:50] + '...') if len(clean_front) > 50 else clean_front
                rec.name = f"{rec.node_id.name or 'Node'}: {truncated}"
            elif rec.node_id:
                rec.name = f"{rec.node_id.name} Flashcard"
            else:
                rec.name = f"Flashcard #{rec.id or rec.sequence}"
