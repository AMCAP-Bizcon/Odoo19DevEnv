# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError


class KmsQuizWizard(models.TransientModel):
    """Wizard allowing learners to take a quiz on a knowledge node."""

    _name = 'kms.quiz.wizard'
    _description = 'KMS Quiz Wizard'
    _rec_name = 'name'

    name = fields.Char(string='Name', compute='_compute_name')
    user_node_id = fields.Many2one(
        'kms.user.node',
        string='User Node Progress',
        required=True,
    )
    node_id = fields.Many2one(
        'kms.node',
        string='Knowledge Node',
        related='user_node_id.node_id',
        readonly=True,
    )
    line_ids = fields.One2many(
        'kms.quiz.wizard.line',
        'wizard_id',
        string='Questions',
    )

    @api.depends('node_id.name')
    def _compute_name(self):
        for rec in self:
            rec.name = f"Quiz: {rec.node_id.name}" if rec.node_id else "Quiz"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        user_node_id = res.get('user_node_id') or self.env.context.get('default_user_node_id')
        if not user_node_id and self.env.context.get('active_model') == 'kms.user.node':
            user_node_id = self.env.context.get('active_id')

        if user_node_id:
            user_node = self.env['kms.user.node'].browse(user_node_id)
            if user_node.exists():
                res['user_node_id'] = user_node.id
                if 'line_ids' in fields_list:
                    lines = [
                        (0, 0, {'question_id': question.id})
                        for question in user_node.node_id.sudo().quiz_question_ids
                    ]
                    res['line_ids'] = lines
        return res

    def action_submit(self):
        """Submit the quiz answers and compute mastery progress."""
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_("There are no quiz questions available for this node."))

        unanswered = self.line_ids.filtered(lambda l: not l.selected_answer_id)
        if unanswered:
            raise UserError(_("Please answer all questions before submitting."))

        answers = [
            {
                'question_id': line.question_id.id,
                'answer_id': line.selected_answer_id.id,
            }
            for line in self.line_ids
        ]

        attempt = self.user_node_id.action_submit_quiz(answers)

        score_percent = int(round(attempt.score * 100))
        threshold_percent = int(round(self.node_id.mastery_threshold * 100))

        if attempt.passed:
            message = _(
                "Congratulations! You passed the quiz with a score of %s%% (Mastery threshold: %s%%).",
                score_percent,
                threshold_percent,
            )
            message_type = 'success'
        else:
            message = _(
                "You scored %s%%. The mastery threshold is %s%%. Please review the material and try again.",
                score_percent,
                threshold_percent,
            )
            message_type = 'warning'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Quiz Result"),
                'message': message,
                'type': message_type,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }


class KmsQuizWizardLine(models.TransientModel):
    """Line item representing a question in the quiz wizard."""

    _name = 'kms.quiz.wizard.line'
    _description = 'KMS Quiz Wizard Line'
    _rec_name = 'name'

    name = fields.Char(string='Name', compute='_compute_name')
    wizard_id = fields.Many2one(
        'kms.quiz.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    question_id = fields.Many2one(
        'kms.quiz.question',
        string='Question',
        required=True,
        ondelete='cascade',
    )
    question_text = fields.Html(
        string='Question Text',
        related='question_id.question_text',
        readonly=True,
    )
    selected_answer_id = fields.Many2one(
        'kms.quiz.answer',
        string='Selected Answer',
        domain="[('question_id', '=', question_id)]",
    )

    @api.depends('question_id.name')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.question_id.name if rec.question_id else "Question Line"
