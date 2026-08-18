# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class KmsFlashcard(models.Model):
    """A flashcard belonging to a knowledge node for spaced repetition."""

    _name = 'kms.flashcard'
    _description = 'KMS Flashcard'
    _order = 'sequence, id'

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
