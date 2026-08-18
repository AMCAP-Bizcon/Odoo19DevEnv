# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError


class KmsUserNode(models.Model):
    """Per-user progress on each knowledge node."""

    _name = 'kms.user.node'
    _description = 'KMS User Node Progress'
    _order = 'node_id'

    user_id = fields.Many2one(
        'res.users',
        string='Learner',
        required=True,
        index=True,
    )
    node_id = fields.Many2one(
        'kms.node',
        string='Knowledge Node',
        required=True,
        ondelete='cascade',
        index=True,
    )
    state = fields.Selection(
        [
            ('locked', 'Locked'),
            ('unlocked', 'Unlocked'),
            ('mastered', 'Mastered'),
        ],
        string='State',
        default='locked',
        required=True,
    )
    best_quiz_score = fields.Float(string='Best Quiz Score')
    mastered_date = fields.Datetime(string='Mastered Date')

    _user_node_unique = models.Constraint(
        'UNIQUE(user_id, node_id)',
        'A user can only have one progress record per node.',
    )

    @api.model
    def action_check_unlock(self, user, node):
        """
        Check if all prerequisites of ``node`` have been mastered by ``user``.
        If so, transition the user's node state from 'locked' to 'unlocked'.
        """
        if not node.prerequisite_ids:
            # No prerequisites → already unlocked by default
            return

        # Check if all prerequisites are mastered
        mastered_prereqs = self.sudo().search_count([
            ('user_id', '=', user.id),
            ('node_id', 'in', node.prerequisite_ids.ids),
            ('state', '=', 'mastered'),
        ])
        if mastered_prereqs == len(node.prerequisite_ids):
            user_node = self.sudo().search([
                ('user_id', '=', user.id),
                ('node_id', '=', node.id),
            ], limit=1)
            if user_node and user_node.state == 'locked':
                user_node.write({'state': 'unlocked'})

    def action_submit_quiz(self, answers):
        """
        Submit a quiz attempt for the current user-node record.

        Args:
            answers: list of dicts with keys 'question_id' and 'answer_id'

        Returns:
            The created kms.quiz.attempt record.
        """
        self.ensure_one()

        if self.state == 'locked':
            raise UserError(
                _("You cannot take a quiz on a locked node. "
                  "Complete the prerequisites first.")
            )

        # Create the attempt
        attempt_lines = []
        for ans in answers:
            attempt_lines.append((0, 0, {
                'question_id': ans['question_id'],
                'selected_answer_id': ans['answer_id'],
            }))

        # Compute score
        total = len(answers)
        if total == 0:
            raise UserError(_("No answers provided."))

        correct = 0
        for ans in answers:
            answer_rec = self.env['kms.quiz.answer'].sudo().browse(ans['answer_id'])
            if answer_rec.is_correct:
                correct += 1

        score = correct / total

        attempt = self.env['kms.quiz.attempt'].sudo().create({
            'user_id': self.user_id.id,
            'node_id': self.node_id.id,
            'score': score,
            'answer_line_ids': attempt_lines,
        })

        # Update best score
        if score > self.best_quiz_score:
            self.write({'best_quiz_score': score})

        # Check if passed
        if score >= self.node_id.mastery_threshold:
            self.write({
                'state': 'mastered',
                'mastered_date': fields.Datetime.now(),
            })

            # Auto-create flashcard progress records
            UserFlashcard = self.env['kms.user.flashcard'].sudo()
            for flashcard in self.node_id.sudo().flashcard_ids:
                existing = UserFlashcard.search([
                    ('user_id', '=', self.user_id.id),
                    ('flashcard_id', '=', flashcard.id),
                ], limit=1)
                if not existing:
                    UserFlashcard.create({
                        'user_id': self.user_id.id,
                        'flashcard_id': flashcard.id,
                        'state': 'new',
                    })

            # Trigger unlock check on all dependents
            for dependent in self.node_id.dependent_ids:
                self.action_check_unlock(self.user_id, dependent)

        return attempt
