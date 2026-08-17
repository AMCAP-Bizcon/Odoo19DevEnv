# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import api, fields, models

from ..utils.fsrs import (
    CardState,
    Rating,
    State,
    compute_retrievability,
    schedule,
)


class KmsUserFlashcard(models.Model):
    """Per-user FSRS state for each flashcard. Implements Modern FSRS scheduling."""

    _name = 'kms.user.flashcard'
    _description = 'KMS User Flashcard Progress'
    _order = 'next_review_date, id'

    user_id = fields.Many2one(
        'res.users',
        string='Learner',
        required=True,
        index=True,
    )
    flashcard_id = fields.Many2one(
        'kms.flashcard',
        string='Flashcard',
        required=True,
        ondelete='cascade',
        index=True,
    )
    state = fields.Selection(
        [
            ('new', 'New'),
            ('learning', 'Learning'),
            ('review', 'Review'),
            ('relearning', 'Relearning'),
        ],
        string='FSRS State',
        default='new',
        required=True,
    )
    difficulty = fields.Float(
        string='Difficulty (D)',
        default=5.0,
        help='FSRS difficulty parameter. Range 1–10.',
    )
    stability = fields.Float(
        string='Stability (S)',
        default=0.0,
        help='FSRS stability in days. Time until retrievability drops to 90%.',
    )
    retrievability = fields.Float(
        string='Retrievability (R)',
        compute='_compute_retrievability',
        help='Current probability of recall, computed on the fly.',
    )
    elapsed_days = fields.Integer(
        string='Elapsed Days',
        default=0,
        help='Days since last review.',
    )
    scheduled_days = fields.Integer(
        string='Scheduled Days',
        default=0,
        help='The interval that was scheduled.',
    )
    reps = fields.Integer(
        string='Total Reviews',
        default=0,
    )
    lapses = fields.Integer(
        string='Lapses',
        default=0,
        help='Times the card was forgotten (rating = Again).',
    )
    last_review_date = fields.Datetime(string='Last Review Date')
    next_review_date = fields.Date(string='Next Review Date')

    _user_flashcard_unique = models.Constraint(
        'UNIQUE(user_id, flashcard_id)',
        'A user can only have one progress record per flashcard.',
    )

    @api.depends('stability', 'last_review_date')
    def _compute_retrievability(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.stability <= 0 or not rec.last_review_date:
                rec.retrievability = 0.0
            else:
                elapsed = (now - rec.last_review_date).days
                rec.retrievability = compute_retrievability(
                    rec.stability, elapsed
                )

    def _to_card_state(self):
        """Convert the record to a CardState dataclass for the FSRS engine."""
        self.ensure_one()
        state_map = {
            'new': State.NEW,
            'learning': State.LEARNING,
            'review': State.REVIEW,
            'relearning': State.RELEARNING,
        }
        return CardState(
            state=state_map.get(self.state, State.NEW),
            difficulty=self.difficulty,
            stability=self.stability,
            elapsed_days=self.elapsed_days,
            scheduled_days=self.scheduled_days,
            reps=self.reps,
            lapses=self.lapses,
        )

    def action_review(self, rating):
        """
        Process a flashcard review.

        Args:
            rating: int, 1=Again, 2=Hard, 3=Good, 4=Easy
        """
        self.ensure_one()
        now = fields.Datetime.now()

        # Compute elapsed days since last review
        if self.last_review_date:
            elapsed = (now - self.last_review_date).days
        else:
            elapsed = 0

        # Run FSRS scheduling
        card_state = self._to_card_state()
        new_state = schedule(
            state=card_state,
            rating=rating,
            elapsed_days=elapsed,
            desired_retention=0.9,
        )

        # Map FSRS state back to selection
        state_rmap = {
            State.NEW: 'new',
            State.LEARNING: 'learning',
            State.REVIEW: 'review',
            State.RELEARNING: 'relearning',
        }

        # Compute next review date
        next_review = fields.Date.today() + timedelta(
            days=new_state.scheduled_days
        )

        self.write({
            'state': state_rmap.get(new_state.state, 'new'),
            'difficulty': new_state.difficulty,
            'stability': new_state.stability,
            'elapsed_days': elapsed,
            'scheduled_days': new_state.scheduled_days,
            'reps': new_state.reps,
            'lapses': new_state.lapses,
            'last_review_date': now,
            'next_review_date': next_review,
        })

    def action_rate_again(self):
        """Rate flashcard as Again (1)."""
        self.action_review(Rating.AGAIN)

    def action_rate_hard(self):
        """Rate flashcard as Hard (2)."""
        self.action_review(Rating.HARD)

    def action_rate_good(self):
        """Rate flashcard as Good (3)."""
        self.action_review(Rating.GOOD)

    def action_rate_easy(self):
        """Rate flashcard as Easy (4)."""
        self.action_review(Rating.EASY)
