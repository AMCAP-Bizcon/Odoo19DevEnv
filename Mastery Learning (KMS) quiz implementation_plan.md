# Add Quiz Wizard UI to KMS Mastery Module

This implementation plan covers the addition of a user-facing Quiz Wizard, allowing learners to take a quiz directly from their "My Progress" (Node) views.

## Open Questions

None at this time.

## Proposed Changes

### Database Access Rights

#### [MODIFY] [ir.model.access.csv](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/security/ir.model.access.csv)
- Add read/write/create/unlink permissions for `kms.quiz.wizard` and `kms.quiz.wizard.line` for both learners and instructors.

### Python Backend

#### [MODIFY] [\_\_init\_\_.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/__init__.py)
- Import the new `wizard` directory.

#### [NEW] [wizard/\_\_init\_\_.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/wizard/__init__.py)
- Import `kms_quiz_wizard`.

#### [NEW] [wizard/kms_quiz_wizard.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/wizard/kms_quiz_wizard.py)
- Define `kms.quiz.wizard` (TransientModel):
    - `user_node_id`: Many2one to `kms.user.node`.
    - `node_id`: Many2one to `kms.node`.
    - `line_ids`: One2many to `kms.quiz.wizard.line`.
    - `action_submit()` method: Prepares the selected answers and passes them to `user_node_id.action_submit_quiz(answers)`, then shows a notification or reloads the page.
    - Default function to populate `line_ids` with questions belonging to the `node_id`.
- Define `kms.quiz.wizard.line` (TransientModel):
    - `wizard_id`: Many2one to `kms.quiz.wizard`.
    - `question_id`: Many2one to `kms.quiz.question`.
    - `question_text`: Related string for display.
    - `selected_answer_id`: Many2one to `kms.quiz.answer` with a domain restricted to `[('question_id', '=', question_id)]`.

### Views and Manifest

#### [NEW] [wizard/kms_quiz_wizard_views.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/wizard/kms_quiz_wizard_views.xml)
- Define the `ir.ui.view` form for `kms.quiz.wizard`.
    - Render the lines using a list view where the user can pick the `selected_answer_id`.
- Define the `ir.actions.act_window` for the wizard with `target="new"` to open as a modal popup.

#### [MODIFY] [\_\_manifest\_\_.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/__manifest__.py)
- Add `wizard/kms_quiz_wizard_views.xml` to the `data` array **before** `views/kms_learner_views.xml` to ensure the action is loaded before being referenced.

#### [MODIFY] [views/kms_learner_views.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/views/kms_learner_views.xml)
- Add a `<header>` block to `kms_user_node_view_form`.
- Inside the header, add a "Take Quiz" `<button>` of `type="action"` pointing to the new wizard action.
- The button will be invisible if `state == 'locked'`.

## Verification Plan

### Manual Verification
1. Log in as a Learner.
2. Navigate to "My Progress" -> Open an "unlocked" or "mastered" Node.
3. Verify the "Take Quiz" button appears.
4. Click "Take Quiz" and verify the wizard popup displays questions associated with the node.
5. Select answers and submit.
6. Verify the attempt score updates the node progress, and it transitions to "mastered" if the score >= threshold.
