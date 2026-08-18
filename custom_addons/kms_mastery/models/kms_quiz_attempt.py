# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class KmsQuizAttempt(models.Model):
    """Records every quiz attempt for analytics and mastery tracking."""

    _name = 'kms.quiz.attempt'
    _description = 'KMS Quiz Attempt'
    _order = 'date desc, id desc'

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

    @api.depends('score', 'node_id.mastery_threshold')
    def _compute_passed(self):
        for rec in self:
            rec.passed = rec.score >= rec.node_id.mastery_threshold


class KmsQuizAttemptLine(models.Model):
    """Individual answer given in a quiz attempt."""

    _name = 'kms.quiz.attempt.line'
    _description = 'KMS Quiz Attempt Line'

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

    @api.depends('selected_answer_id.is_correct')
    def _compute_is_correct(self):
        for rec in self:
            rec.is_correct = rec.selected_answer_id.sudo().is_correct if rec.selected_answer_id else False
