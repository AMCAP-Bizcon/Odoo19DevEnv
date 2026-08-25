# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

import base64
import json
import logging
import urllib.request
import urllib.error

from odoo import api, fields, models, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Maximum inline PDF size for Gemini API (20 MB)
MAX_PDF_SIZE_BYTES = 20 * 1024 * 1024

SYSTEM_PROMPT = """\
You are an expert educational content creator. Analyze the provided source \
material (PDF document) and generate granular structured learning content.

For each distinct atomic topic or concept in the material, create a knowledge node with:
1. A clear, concise name (max 3 words)
2. A detailed explaination of the topic in html format
3. Flashcards (question/prompt on front, answer on back) for key facts and concepts
4. Quiz questions — either multiple choice (MCQ) or true/false (TF)

Guidelines:
- Create meaningful, distinct atomic nodes that represent separate bite sized topics or concepts.
- Flashcards should test recall of important facts, definitions, and concepts.
- MCQ questions MUST have exactly 4 answer options with exactly 1 correct answer.
- True/False questions MUST have exactly 2 options ("True" and "False") with \
exactly 1 correct.
- All content must be directly derived from the source material.
- Use clear, unambiguous language.

Respond with valid JSON matching this schema:
{
  "nodes": [
    {
      "name": "Topic Name",
      "description": "Detailed description of the topic in html format.",
      "flashcards": [
        {"front": "Question or prompt", "back": "Answer or explanation"}
      ],
      "questions": [
        {
          "question_text": "The question text?",
          "type": "mcq",
          "answers": [
            {"text": "Option A", "is_correct": false},
            {"text": "Option B", "is_correct": true},
            {"text": "Option C", "is_correct": false},
            {"text": "Option D", "is_correct": false}
          ]
        }
      ]
    }
  ]
}"""


# ============================================================
#                    MAIN WIZARD
# ============================================================

class KmsAiGenerateWizard(models.TransientModel):
    _name = 'kms.ai.generate.wizard'
    _description = 'AI Content Generation Wizard'

    state = fields.Selection(
        selection=[
            ('upload', 'Upload'),
            ('preview', 'Preview'),
            ('done', 'Done'),
        ],
        default='upload',
        required=True,
    )

    # ---- Upload fields ----
    source_file = fields.Binary(
        string="Source PDF",
        attachment=False,
    )
    source_filename = fields.Char(string="Filename")
    course_id = fields.Many2one(
        'kms.course',
        string="Link to Course",
        help="Optional. Generated nodes will be added to this course.",
    )
    num_flashcards = fields.Integer(
        string="Flashcards per Node",
        default=5,
        help="Approximate number of flashcards to generate per node.",
    )
    num_questions = fields.Integer(
        string="Questions per Node",
        default=5,
        help="Approximate number of quiz questions to generate per node.",
    )

    # ---- Preview fields (One2many to transient lines) ----
    node_line_ids = fields.One2many(
        'kms.ai.generate.node.line', 'wizard_id',
        string="Generated Nodes",
    )
    flashcard_line_ids = fields.One2many(
        'kms.ai.generate.flashcard.line', 'wizard_id',
        string="Generated Flashcards",
    )
    question_line_ids = fields.One2many(
        'kms.ai.generate.question.line', 'wizard_id',
        string="Generated Questions",
    )

    # ---- Result fields ----
    raw_response = fields.Text(string="Raw AI Response")
    status_message = fields.Html(
        string="Status",
        compute='_compute_status_message',
    )
    created_node_count = fields.Integer(default=0)
    created_flashcard_count = fields.Integer(default=0)
    created_question_count = fields.Integer(default=0)

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------

    @api.depends('state', 'created_node_count', 'created_flashcard_count',
                 'created_question_count')
    def _compute_status_message(self):
        for wizard in self:
            if wizard.state == 'done':
                wizard.status_message = (
                    '<div class="alert alert-success mb-0" role="status">'
                    '<h4 class="alert-heading">'
                    '<i class="fa fa-check-circle"/> Content Generated Successfully!</h4>'
                    '<p class="mb-0"><strong>%d</strong> node(s), '
                    '<strong>%d</strong> flashcard(s), '
                    'and <strong>%d</strong> question(s) were created.</p></div>'
                ) % (
                    wizard.created_node_count,
                    wizard.created_flashcard_count,
                    wizard.created_question_count,
                )
            else:
                wizard.status_message = False

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_generate(self):
        """Extract PDF → call Gemini → populate preview lines."""
        self.ensure_one()

        # Validate upload
        if not self.source_file:
            raise UserError(_("Please upload a PDF file."))
        if self.source_filename and not self.source_filename.lower().endswith('.pdf'):
            raise UserError(_("Only PDF files are supported. Please upload a .pdf file."))

        # Check file size (base64 is ~4/3 of raw size)
        file_b64 = self.source_file
        if isinstance(file_b64, bytes):
            file_b64 = file_b64.decode('ascii')
        raw_size = len(base64.b64decode(file_b64))
        if raw_size > MAX_PDF_SIZE_BYTES:
            raise UserError(_(
                "The uploaded PDF is too large (%(size).1f MB). "
                "Gemini supports up to %(max)d MB for inline documents.",
                size=raw_size / (1024 * 1024),
                max=MAX_PDF_SIZE_BYTES // (1024 * 1024),
            ))

        # Read API settings
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('kms_mastery.ai_api_key', '')
        model_name = ICP.get_param('kms_mastery.ai_model', 'gemini-2.0-flash')
        if not api_key:
            raise UserError(_(
                "Gemini API key is not configured.\n"
                "Go to Settings → KMS Mastery to set your API key."
            ))

        # Call Gemini
        try:
            response_data = self._call_gemini(file_b64, api_key, model_name)
        except UserError:
            raise
        except Exception as e:
            _logger.exception("Unexpected error during AI generation")
            raise UserError(_("AI generation failed: %s") % str(e))

        # Populate preview
        self._populate_preview(response_data)
        self.raw_response = json.dumps(response_data, indent=2, ensure_ascii=False)
        self.state = 'preview'

        return self._reopen()

    def action_confirm(self):
        """Create actual kms.node / kms.flashcard / kms.quiz.question records."""
        self.ensure_one()

        Node = self.env['kms.node']
        Flashcard = self.env['kms.flashcard']
        Question = self.env['kms.quiz.question']
        Answer = self.env['kms.quiz.answer']

        selected_nodes = self.node_line_ids.filtered('selected')
        if not selected_nodes:
            raise UserError(_("Please select at least one node to create."))

        created_nodes = self.env['kms.node']
        fc_count = 0
        q_count = 0

        for node_line in selected_nodes:
            node = Node.create({
                'name': node_line.name,
                'description': '<p>%s</p>' % node_line.description if node_line.description else '',
            })
            created_nodes |= node

            # Flashcards
            for fc in node_line.flashcard_line_ids.filtered('selected'):
                Flashcard.create({
                    'node_id': node.id,
                    'front': '<p>%s</p>' % fc.front if fc.front else '',
                    'back': '<p>%s</p>' % fc.back if fc.back else '',
                    'sequence': fc.sequence,
                })
                fc_count += 1

            # Questions + answers
            for ql in node_line.question_line_ids.filtered('selected'):
                question = Question.create({
                    'node_id': node.id,
                    'question_text': '<p>%s</p>' % ql.question_text if ql.question_text else '',
                    'type': ql.question_type,
                    'sequence': ql.sequence,
                })
                for al in ql.answer_line_ids:
                    Answer.create({
                        'question_id': question.id,
                        'text': al.text,
                        'is_correct': al.is_correct,
                        'sequence': al.sequence,
                    })
                q_count += 1

        # Link to course
        if self.course_id and created_nodes:
            self.course_id.write({
                'node_ids': [(4, n.id) for n in created_nodes],
            })

        self.write({
            'created_node_count': len(created_nodes),
            'created_flashcard_count': fc_count,
            'created_question_count': q_count,
            'state': 'done',
        })

        return self._reopen()

    def action_back(self):
        """Return to upload state for re-upload or re-generation."""
        self.ensure_one()
        self.state = 'upload'
        return self._reopen()

    def action_view_nodes(self):
        """Open a list of the nodes just created (best-effort: recent by this user)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Generated Nodes"),
            'res_model': 'kms.node',
            'view_mode': 'list,form',
            'target': 'current',
        }

    # ------------------------------------------------------------------
    # Gemini API
    # ------------------------------------------------------------------

    def _call_gemini(self, pdf_b64, api_key, model_name):
        """Send the PDF to Gemini and return parsed JSON response."""
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "%s:generateContent?key=%s" % (model_name, api_key)
        )

        user_prompt = (
            "Analyze the attached PDF document and generate learning content. "
            "Create up to %d flashcards and up to %d quiz questions per node/topic. "
            "Respond ONLY with the JSON object — no markdown fences, no extra text."
        ) % (self.num_flashcards, self.num_questions)

        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "text": user_prompt,
                    },
                ],
            }],
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}],
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.7,
            },
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, data=data,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )

        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='replace')
            _logger.error("Gemini API HTTP %s: %s", e.code, body)
            raise UserError(
                _("Gemini API error (HTTP %(code)s): %(body)s",
                  code=e.code, body=body[:500])
            )
        except urllib.error.URLError as e:
            raise UserError(
                _("Cannot reach Gemini API: %s") % str(e.reason)
            )

        # Parse response structure
        try:
            text = (
                result['candidates'][0]['content']['parts'][0]['text']
            )
            return json.loads(text)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            _logger.error(
                "Failed to parse Gemini response: %s\nRaw result: %s",
                e, json.dumps(result, indent=2, ensure_ascii=False)[:2000],
            )
            raise UserError(_(
                "The AI returned an invalid response. Please try again.\n"
                "Technical detail: %s"
            ) % str(e))

    # ------------------------------------------------------------------
    # Preview population
    # ------------------------------------------------------------------

    def _populate_preview(self, data):
        """Create transient preview records from the parsed AI JSON."""
        # Clear any previous preview
        self.node_line_ids.unlink()
        self.flashcard_line_ids.unlink()
        self.question_line_ids.unlink()

        nodes = data.get('nodes', [])
        if not nodes:
            raise UserError(_(
                "The AI did not generate any nodes from this document. "
                "The document may be too short or not educational in nature."
            ))

        NodeLine = self.env['kms.ai.generate.node.line']
        FcLine = self.env['kms.ai.generate.flashcard.line']
        QLine = self.env['kms.ai.generate.question.line']
        ALine = self.env['kms.ai.generate.answer.line']

        for seq, nd in enumerate(nodes, start=1):
            node_line = NodeLine.create({
                'wizard_id': self.id,
                'sequence': seq,
                'name': (nd.get('name') or _("Untitled Node"))[:200],
                'description': nd.get('description', ''),
                'selected': True,
            })

            for fc_seq, fc in enumerate(nd.get('flashcards', []), start=1):
                FcLine.create({
                    'wizard_id': self.id,
                    'node_line_id': node_line.id,
                    'sequence': fc_seq,
                    'front': fc.get('front', ''),
                    'back': fc.get('back', ''),
                    'selected': True,
                })

            for q_seq, q in enumerate(nd.get('questions', []), start=1):
                q_type = q.get('type', 'mcq')
                if q_type not in ('mcq', 'tf'):
                    q_type = 'mcq'

                q_line = QLine.create({
                    'wizard_id': self.id,
                    'node_line_id': node_line.id,
                    'sequence': q_seq,
                    'question_text': q.get('question_text', ''),
                    'question_type': q_type,
                    'selected': True,
                })

                for a_seq, a in enumerate(q.get('answers', []), start=1):
                    ALine.create({
                        'question_line_id': q_line.id,
                        'sequence': a_seq,
                        'text': a.get('text', ''),
                        'is_correct': bool(a.get('is_correct')),
                    })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reopen(self):
        """Return an action that re-opens this wizard in a dialog."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


# ============================================================
#                  PREVIEW LINE MODELS
# ============================================================

class KmsAiGenerateNodeLine(models.TransientModel):
    _name = 'kms.ai.generate.node.line'
    _description = 'AI Generate — Node Preview'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'kms.ai.generate.wizard', required=True, ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Node Name", required=True)
    description = fields.Text(string="Description")
    selected = fields.Boolean(string="Include", default=True)

    flashcard_line_ids = fields.One2many(
        'kms.ai.generate.flashcard.line', 'node_line_id',
        string="Flashcards",
    )
    question_line_ids = fields.One2many(
        'kms.ai.generate.question.line', 'node_line_id',
        string="Questions",
    )
    flashcard_count = fields.Integer(
        string="Flashcards", compute='_compute_counts',
    )
    question_count = fields.Integer(
        string="Questions", compute='_compute_counts',
    )

    @api.depends('flashcard_line_ids', 'question_line_ids')
    def _compute_counts(self):
        for line in self:
            line.flashcard_count = len(line.flashcard_line_ids)
            line.question_count = len(line.question_line_ids)


class KmsAiGenerateFlashcardLine(models.TransientModel):
    _name = 'kms.ai.generate.flashcard.line'
    _description = 'AI Generate — Flashcard Preview'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'kms.ai.generate.wizard', required=True, ondelete='cascade',
    )
    node_line_id = fields.Many2one(
        'kms.ai.generate.node.line', string="Node", ondelete='cascade',
    )
    node_name = fields.Char(related='node_line_id.name', string="Node")
    sequence = fields.Integer(default=10)
    front = fields.Text(string="Front (Question)")
    back = fields.Text(string="Back (Answer)")
    selected = fields.Boolean(string="Include", default=True)


class KmsAiGenerateQuestionLine(models.TransientModel):
    _name = 'kms.ai.generate.question.line'
    _description = 'AI Generate — Question Preview'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'kms.ai.generate.wizard', required=True, ondelete='cascade',
    )
    node_line_id = fields.Many2one(
        'kms.ai.generate.node.line', string="Node", ondelete='cascade',
    )
    node_name = fields.Char(related='node_line_id.name', string="Node")
    sequence = fields.Integer(default=10)
    question_text = fields.Text(string="Question")
    question_type = fields.Selection(
        selection=[('mcq', 'Multiple Choice'), ('tf', 'True / False')],
        string="Type",
        default='mcq',
    )
    selected = fields.Boolean(string="Include", default=True)

    answer_line_ids = fields.One2many(
        'kms.ai.generate.answer.line', 'question_line_id',
        string="Answer Options",
    )


class KmsAiGenerateAnswerLine(models.TransientModel):
    _name = 'kms.ai.generate.answer.line'
    _description = 'AI Generate — Answer Preview'
    _order = 'sequence, id'

    question_line_id = fields.Many2one(
        'kms.ai.generate.question.line', required=True, ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    text = fields.Char(string="Answer Text", required=True)
    is_correct = fields.Boolean(string="Correct")
