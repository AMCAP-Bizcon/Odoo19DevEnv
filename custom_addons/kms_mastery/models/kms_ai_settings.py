# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    kms_ai_api_key = fields.Char(
        string="Gemini API Key",
        config_parameter='kms_mastery.ai_api_key',
        help="Your Google Gemini API key. Get one from https://aistudio.google.com/apikey",
    )
    kms_ai_model = fields.Char(
        string="Gemini Model",
        config_parameter='kms_mastery.ai_model',
        default='gemini-2.0-flash',
        help="The Gemini model to use for content generation (e.g. gemini-2.0-flash, gemini-2.5-pro).",
    )
