# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class KmsUserMilestone(models.Model):
    """Per-user milestone submission with chatter and activity support."""

    _name = 'kms.user.milestone'
    _description = 'KMS User Milestone Submission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'submission_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Submission Name', compute='_compute_name', store=True)
    user_id = fields.Many2one(
        'res.users',
        string='Learner',
        required=True,
        index=True,
    )
    milestone_id = fields.Many2one(
        'kms.milestone',
        string='Milestone',
        required=True,
        ondelete='cascade',
        index=True,
    )
    state = fields.Selection(
        [
            ('pending', 'Pending Submission'),
            ('submitted', 'Submitted'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
        ],
        string='Status',
        default='pending',
        required=True,
        tracking=True,
    )
    submission_file_ids = fields.Many2many(
        'ir.attachment',
        'kms_user_milestone_attachment_rel',
        'user_milestone_id',
        'attachment_id',
        string='Submission Files',
    )
    submission_url = fields.Char(string='Submission URL')
    submission_date = fields.Datetime(string='Submission Date')
    grade_date = fields.Datetime(string='Grade Date')
    instructor_feedback = fields.Html(string='Instructor Feedback')

    _user_milestone_unique = models.Constraint(
        'UNIQUE(user_id, milestone_id)',
        'A user can only have one submission record per milestone.',
    )

    # Related fields for display
    course_id = fields.Many2one(
        related='milestone_id.course_id',
        string='Course',
        store=True,
    )
    milestone_name = fields.Char(
        related='milestone_id.name',
        string='Milestone Name',
    )

    @api.depends('user_id.name', 'milestone_id.name')
    def _compute_name(self):
        for rec in self:
            user_name = rec.user_id.name or 'Learner'
            ms_name = rec.milestone_id.name or 'Milestone'
            rec.name = f"{ms_name} ({user_name})"

    def action_submit(self):
        """Mark the milestone as submitted by the learner."""
        self.ensure_one()
        self.write({
            'state': 'submitted',
            'submission_date': fields.Datetime.now(),
        })

    def action_pass(self):
        """Mark the milestone as passed by the instructor."""
        self.ensure_one()
        self.write({
            'state': 'passed',
            'grade_date': fields.Datetime.now(),
        })

    def action_fail(self):
        """Mark the milestone as failed by the instructor."""
        self.ensure_one()
        self.write({
            'state': 'failed',
            'grade_date': fields.Datetime.now(),
        })

    def action_reset_to_pending(self):
        """Reset to pending so learner can resubmit."""
        self.ensure_one()
        self.write({
            'state': 'pending',
            'grade_date': False,
        })

    @api.model
    def _cron_send_milestone_reminders(self):
        """
        Daily cron job: send reminder emails for milestones in 'submitted'
        state that have not yet been graded.
        """
        submitted = self.search([('state', '=', 'submitted')])
        template = self.env.ref(
            'kms_mastery.milestone_reminder_template',
            raise_if_not_found=False,
        )
        if not template:
            _logger.warning(
                "KMS: Mail template 'milestone_reminder_template' not found. "
                "Skipping milestone reminders."
            )
            return

        for rec in submitted:
            instructor = rec.milestone_id._get_instructor()
            # Send to learner
            if rec.user_id.partner_id:
                template.send_mail(
                    rec.id,
                    force_send=False,
                    email_values={
                        'email_to': rec.user_id.partner_id.email,
                    },
                )
            # Send to instructor
            if instructor and instructor.partner_id:
                template.send_mail(
                    rec.id,
                    force_send=False,
                    email_values={
                        'email_to': instructor.partner_id.email,
                    },
                )
