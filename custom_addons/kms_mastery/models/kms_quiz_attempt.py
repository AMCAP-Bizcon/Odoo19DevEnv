# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class KmsQuizAttempt(models.Model):
    """Records every quiz attempt for analytics and mastery tracking."""

    _name = 'kms.quiz.attempt'
    _description = 'KMS Quiz Attempt'
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Attempt', compute='_compute_name', store=True)
    user_id = fields.Many2one(
        'res.users',
        string='Learner',
        required=True,
        default=lambda self: self.env.user,
    )
    node_id = fields.Many2one(
        'kms.node',
        string='Knowledge Node',
        required=True,
        ondelete='cascade',
    )
    score = fields.Float(
        string='Score',
        help='Percentage score (0.0–1.0)',
    )
    passed = fields.Boolean(
        string='Passed',
        compute='_compute_passed',
        store=True,
    )
    date = fields.Datetime(
        string='Attempt Date',
        default=fields.Datetime.now,
    )
    answer_line_ids = fields.One2many(
        'kms.quiz.attempt.line',
        'attempt_id',
        string='Answer Lines',
    )

    @api.depends('user_id.name', 'node_id.name', 'date')
    def _compute_name(self):
        for rec in self:
            date_str = rec.date.strftime('%Y-%m-%d %H:%M') if rec.date else ''
            user_name = rec.user_id.name or 'Learner'
            node_name = rec.node_id.name or 'Node'
            rec.name = f"{node_name} - {user_name} ({date_str})" if date_str else f"{node_name} - {user_name}"

    @api.depends('score', 'node_id.mastery_threshold')
    def _compute_passed(self):
        for rec in self:
            rec.passed = rec.score >= rec.node_id.mastery_threshold


class KmsQuizAttemptLine(models.Model):
    """Individual answer given in a quiz attempt."""

    _name = 'kms.quiz.attempt.line'
    _description = 'KMS Quiz Attempt Line'
    _rec_name = 'name'

    name = fields.Char(string='Line', compute='_compute_name')
    attempt_id = fields.Many2one(
        'kms.quiz.attempt',
        string='Attempt',
        required=True,
        ondelete='cascade',
    )
    question_id = fields.Many2one(
        'kms.quiz.question',
        string='Question',
    )
    selected_answer_id = fields.Many2one(
        'kms.quiz.answer',
        string='Selected Answer',
    )
    is_correct = fields.Boolean(
        string='Correct',
        compute='_compute_is_correct',
        store=True,
        groups='kms_mastery.group_kms_instructor',
    )

    @api.depends('question_id.name', 'selected_answer_id.text')
    def _compute_name(self):
        for rec in self:
            q_name = rec.question_id.name or 'Question'
            ans_text = rec.selected_answer_id.text or 'No Answer'
            rec.name = f"{q_name}: {ans_text}"

    @api.depends('selected_answer_id.is_correct')
    def _compute_is_correct(self):
        for rec in self:
            rec.is_correct = rec.selected_answer_id.sudo().is_correct if rec.selected_answer_id else False
