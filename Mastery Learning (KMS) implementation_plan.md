# Mastery Learning Knowledge Management System (KMS) — Odoo 19

## Overview

A custom Odoo 19 Community Edition module (`kms_mastery`) implementing mastery-based learning. Knowledge is structured as a **Directed Acyclic Graph (DAG)** of concept nodes. Learners must demonstrate mastery of prerequisite nodes before unlocking subsequent content. Mastery is established through auto-graded quizzes, maintained via **Modern FSRS** spaced-repetition flashcards, and practically validated through human-graded milestone assignments.

## Architecture Decisions

> [!NOTE]
> - **Spaced Repetition Algorithm**: Modern FSRS (Free Spaced Repetition Scheduler) with the DSR memory model (Difficulty, Stability, Retrievability). Retrievability is computed on-the-fly, not stored.
> - **Milestone Blocking**: Learners are **not blocked** from progressing in unrelated DAG branches while awaiting milestone evaluation. Daily automated reminders are sent to both learner and assigned instructor.
> - **Mastery State Machine**: Passing the quiz (≥ per-node threshold) transitions a node to `Mastered` and auto-generates flashcard progress records. Flashcard reviews maintain long-term retention but **do not gate** DAG progression. Milestones are separate human-evaluated assessments that also **do not block** the DAG.
> - **Content Visibility**: All learners can see node titles and the full DAG structure (so they understand the learning path). Node content (`description`, quiz questions, flashcards, attachments) is only accessible for unlocked/mastered nodes. This is enforced via computed fields, not record rules.

---

## Module Setup

### Location

```
c:\Users\aniru\Documents\Odoo19DevEnv\custom_addons\kms_mastery\
```

> [!IMPORTANT]
> Create the `custom_addons` directory and update [`odoo.conf`](file:///c:/Users/aniru/Documents/Odoo19DevEnv/Docs/odoo.conf) to add it to `addons_path`:
> ```ini
> addons_path = C:\Users\aniru\Documents\Odoo19DevEnv\odoo\addons,C:\Users\aniru\Documents\Odoo19DevEnv\custom_addons
> ```

### Directory Structure

```
kms_mastery/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── kms_course.py
│   ├── kms_node.py
│   ├── kms_quiz_question.py
│   ├── kms_quiz_answer.py
│   ├── kms_quiz_attempt.py
│   ├── kms_flashcard.py
│   ├── kms_milestone.py
│   ├── kms_user_node.py
│   ├── kms_user_flashcard.py
│   └── kms_user_milestone.py
├── views/
│   ├── kms_course_views.xml
│   ├── kms_node_views.xml
│   ├── kms_quiz_views.xml
│   ├── kms_flashcard_views.xml
│   ├── kms_milestone_views.xml
│   ├── kms_learner_views.xml
│   └── kms_menus.xml
├── security/
│   ├── kms_security.xml
│   └── ir.model.access.csv
├── data/
│   ├── ir_cron_data.xml
│   └── mail_template_data.xml
├── demo/
│   └── kms_demo_data.xml
├── static/
│   └── src/
│       └── components/
│           └── dag_viewer/
│               ├── dag_viewer.js
│               ├── dag_viewer.xml
│               └── dag_viewer.scss
└── tests/
    ├── __init__.py
    ├── test_dag_logic.py
    ├── test_mastery_logic.py
    └── test_fsrs_logic.py
```

---

### [NEW] `__manifest__.py`

```python
{
    'name': 'KMS Mastery Learning',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Mastery-based Knowledge Management with DAG, Quizzes, FSRS Flashcards, and Milestones',
    'description': """
Mastery Learning Knowledge Management System
=============================================
- Directed Acyclic Graph (DAG) of knowledge nodes with prerequisite enforcement
- Auto-graded quizzes with configurable mastery thresholds
- Modern FSRS spaced-repetition flashcards for long-term retention
- Human-graded milestone assignments with daily reminder notifications
- Interactive OWL DAG visualization component
    """,
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        # Security (must load first)
        'security/kms_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        # Views
        'views/kms_course_views.xml',
        'views/kms_node_views.xml',
        'views/kms_quiz_views.xml',
        'views/kms_flashcard_views.xml',
        'views/kms_milestone_views.xml',
        'views/kms_learner_views.xml',
        'views/kms_menus.xml',
    ],
    'demo': [
        'demo/kms_demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kms_mastery/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
```

---

## Proposed Changes

### Data Models (`models/`)

All `__init__.py` files must chain-import every model file. Root `__init__.py` imports `from . import models`. `models/__init__.py` imports each model file.

---

#### [NEW] `models/kms_course.py` — `kms.course`

Enrollment scope: groups nodes into learnable courses. Learners enroll in a course and only see nodes within it.

| Field | Type | Details |
|---|---|---|
| `name` | Char | Required |
| `description` | Html | Course overview |
| `active` | Boolean | Default `True`. Enables archive/unarchive |
| `instructor_id` | Many2one → `res.users` | Primary instructor. Domain: `[('groups_id', 'in', [ref('kms_mastery.group_kms_instructor')])]` |
| `node_ids` | Many2many → `kms.node` | Nodes belonging to this course |
| `milestone_ids` | One2many → `kms.milestone` | Milestones in this course (via `course_id`) |
| `learner_ids` | Many2many → `res.users` | Enrolled learners |
| `sequence` | Integer | Default `10` |

- `_order = 'sequence, id'`

---

#### [NEW] `models/kms_node.py` — `kms.node`

The core knowledge concept in the DAG.

| Field | Type | Details |
|---|---|---|
| `name` | Char | Required |
| `description` | Html | Rich text learning content |
| `resource_url` | Char | Optional external link |
| `attachment_ids` | Many2many → `ir.attachment` | Supplementary files |
| `active` | Boolean | Default `True`. Soft-delete support |
| `sequence` | Integer | Default `10` |
| `mastery_threshold` | Float | Default `0.9` (90%). Per-node quiz pass threshold |
| `prerequisite_ids` | Many2many → `kms.node` | Self-referential. Relation table: `kms_node_prerequisite_rel`, columns: `node_id`, `prerequisite_id` |
| `dependent_ids` | Many2many → `kms.node` | Inverse of `prerequisite_ids`. Same relation table, swapped columns: `prerequisite_id`, `node_id` |
| `quiz_question_ids` | One2many → `kms.quiz.question` | Via `node_id` |
| `flashcard_ids` | One2many → `kms.flashcard` | Via `node_id` |
| `quiz_question_count` | Integer | Computed, count of `quiz_question_ids` |
| `flashcard_count` | Integer | Computed, count of `flashcard_ids` |

- `_order = 'sequence, id'`

**Constraints**:
```python
@api.constrains('prerequisite_ids')
def _check_no_cyclic_dependencies(self):
    if self._has_cycle('prerequisite_ids'):
        raise ValidationError(_("Circular prerequisite dependency detected."))
```

---

#### [NEW] `models/kms_quiz_question.py` — `kms.quiz.question`

| Field | Type | Details |
|---|---|---|
| `node_id` | Many2one → `kms.node` | Required, `ondelete='cascade'` |
| `question_text` | Html | Required |
| `type` | Selection | `[('mcq', 'Multiple Choice'), ('tf', 'True/False')]` |
| `answer_ids` | One2many → `kms.quiz.answer` | Via `question_id` |
| `sequence` | Integer | Default `10` |

- `_order = 'sequence, id'`

---

#### [NEW] `models/kms_quiz_answer.py` — `kms.quiz.answer`

| Field | Type | Details |
|---|---|---|
| `question_id` | Many2one → `kms.quiz.question` | Required, `ondelete='cascade'` |
| `text` | Char | Required. The answer option text |
| `is_correct` | Boolean | Default `False` |
| `sequence` | Integer | Default `10` |

- `_order = 'sequence, id'`

---

#### [NEW] `models/kms_quiz_attempt.py` — `kms.quiz.attempt`

Records every quiz attempt for analytics and anti-brute-force tracking.

| Field | Type | Details |
|---|---|---|
| `user_id` | Many2one → `res.users` | Required, default `lambda self: self.env.user` |
| `node_id` | Many2one → `kms.node` | Required, `ondelete='cascade'` |
| `score` | Float | Percentage score (0.0–1.0) |
| `passed` | Boolean | Computed: `score >= node_id.mastery_threshold` |
| `date` | Datetime | Default `fields.Datetime.now` |
| `answer_line_ids` | One2many → `kms.quiz.attempt.line` | Individual answers given |

**Sub-model `kms.quiz.attempt.line`**:

| Field | Type | Details |
|---|---|---|
| `attempt_id` | Many2one → `kms.quiz.attempt` | `ondelete='cascade'` |
| `question_id` | Many2one → `kms.quiz.question` | |
| `selected_answer_id` | Many2one → `kms.quiz.answer` | |
| `is_correct` | Boolean | Computed from `selected_answer_id.is_correct` |

---

#### [NEW] `models/kms_flashcard.py` — `kms.flashcard`

| Field | Type | Details |
|---|---|---|
| `node_id` | Many2one → `kms.node` | Required, `ondelete='cascade'` |
| `front` | Html | Question / prompt side |
| `back` | Html | Answer side |
| `sequence` | Integer | Default `10` |

- `_order = 'sequence, id'`

---

#### [NEW] `models/kms_milestone.py` — `kms.milestone`

Human-graded assignment tied to a set of nodes within a course.

| Field | Type | Details |
|---|---|---|
| `name` | Char | Required |
| `description` | Html | Assignment instructions |
| `course_id` | Many2one → `kms.course` | Required, `ondelete='cascade'` |
| `instructor_id` | Many2one → `res.users` | The instructor responsible for grading. Defaults to `course_id.instructor_id` |
| `node_ids` | Many2many → `kms.node` | The nodes this milestone assesses |
| `sequence` | Integer | Default `10` |

- `_order = 'sequence, id'`

---

#### [NEW] `models/kms_user_node.py` — `kms.user.node`

Per-user progress on each knowledge node.

| Field | Type | Details |
|---|---|---|
| `user_id` | Many2one → `res.users` | Required |
| `node_id` | Many2one → `kms.node` | Required, `ondelete='cascade'` |
| `state` | Selection | `[('locked', 'Locked'), ('unlocked', 'Unlocked'), ('mastered', 'Mastered')]`. Default `'locked'` |
| `best_quiz_score` | Float | Best score across all attempts |
| `mastered_date` | Datetime | When mastery was achieved |

**SQL Constraints**:
```python
_sql_constraints = [
    ('user_node_unique', 'UNIQUE(user_id, node_id)', 'A user can only have one progress record per node.'),
]
```

**Key Methods**:
- `action_check_unlock(user, node)`: Checks if all `node.prerequisite_ids` have state `mastered` in `kms.user.node` for this user. If yes, transitions state to `unlocked`.
- `action_submit_quiz(user, node, answers)`: Creates a `kms.quiz.attempt`, computes score, if `score >= node.mastery_threshold` → sets state to `mastered`, sets `mastered_date`, auto-creates `kms.user.flashcard` records for all `node.flashcard_ids`, and triggers `action_check_unlock` on all `node.dependent_ids`.

---

#### [NEW] `models/kms_user_flashcard.py` — `kms.user.flashcard`

Per-user FSRS state for each flashcard. Implements the **Modern FSRS** scheduling algorithm.

| Field | Type | Details |
|---|---|---|
| `user_id` | Many2one → `res.users` | Required |
| `flashcard_id` | Many2one → `kms.flashcard` | Required, `ondelete='cascade'` |
| `state` | Selection | `[('new', 'New'), ('learning', 'Learning'), ('review', 'Review'), ('relearning', 'Relearning')]`. Default `'new'` |
| `difficulty` | Float | FSRS D parameter. Range 1–10. Default `5.0` |
| `stability` | Float | FSRS S parameter. Days until R drops to 90%. Default `0.0` |
| `retrievability` | Float | **Computed, not stored**. $R = \left(1 + \frac{t}{9 \cdot S}\right)^{-1}$ where $t$ = elapsed days since last review |
| `elapsed_days` | Integer | Days since last review. Default `0` |
| `scheduled_days` | Integer | The interval that was scheduled. Default `0` |
| `reps` | Integer | Total number of reviews. Default `0` |
| `lapses` | Integer | Times the card was forgotten (rating = Again). Default `0` |
| `last_review_date` | Datetime | Timestamp of last review |
| `next_review_date` | Date | Next scheduled review date |

**SQL Constraints**:
```python
_sql_constraints = [
    ('user_flashcard_unique', 'UNIQUE(user_id, flashcard_id)', 'A user can only have one progress record per flashcard.'),
]
```

**FSRS Configuration** (stored at course or system level):
- `desired_retention`: Float, default `0.9`. Target retention probability.
- `fsrs_weights`: Text/Json field storing the 19 FSRS optimizer parameters (w0–w18). Uses default weights initially; can be optimized later from review history.

> [!TIP]
> The FSRS scheduling logic should be implemented as a standalone Python utility (`kms_mastery/utils/fsrs.py`) to keep the model clean. The model calls `fsrs.schedule(card_state, rating)` which returns the new state. This also makes unit testing the algorithm straightforward.

**Key Method**:
- `action_review(rating)`: Called when user rates a flashcard (Again=1, Hard=2, Good=3, Easy=4). Updates all FSRS state fields and computes `next_review_date`.

---

#### [NEW] `models/kms_user_milestone.py` — `kms.user.milestone`

Inherits `mail.thread` and `mail.activity.mixin` for chatter and activity scheduling.

| Field | Type | Details |
|---|---|---|
| `user_id` | Many2one → `res.users` | Required. The learner |
| `milestone_id` | Many2one → `kms.milestone` | Required, `ondelete='cascade'` |
| `state` | Selection | `[('pending', 'Pending Submission'), ('submitted', 'Submitted'), ('passed', 'Passed'), ('failed', 'Failed')]`. Default `'pending'`. Tracked for chatter (`tracking=True`) |
| `submission_file_ids` | Many2many → `ir.attachment` | Learner's submitted files |
| `submission_url` | Char | Optional link to external submission |
| `submission_date` | Datetime | When learner submitted |
| `grade_date` | Datetime | When instructor graded |
| `instructor_feedback` | Html | Instructor's written feedback |

**Inherits**: `mail.thread`, `mail.activity.mixin`

---

### FSRS Utility (`utils/`)

#### [NEW] `kms_mastery/utils/fsrs.py`

Pure Python implementation of the FSRS-5 scheduling algorithm. No Odoo dependencies so it can be unit-tested independently.

Key functions:
- `init_card() → CardState`: Returns default new card state
- `schedule(state: CardState, rating: int, elapsed_days: int, desired_retention: float, weights: list) → CardState`: Computes new difficulty, stability, scheduled_days, state
- `compute_retrievability(stability: float, elapsed_days: int) → float`: The forgetting curve formula

---

### Views and UI (`views/` & `static/`)

#### [NEW] `views/kms_course_views.xml`
- **Form**: Course details, inline list of enrolled learners, linked nodes (Many2many tags widget), linked milestones.
- **Tree**: Name, instructor, learner count.
- **Kanban**: Card per course with progress stats.

#### [NEW] `views/kms_node_views.xml`
- **Form**: Name, description (Html widget), resource URL, attachments, mastery threshold (percentage widget), prerequisites (Many2many tags), inline quiz questions tab, inline flashcards tab.
- **Tree**: Sequence-ordered list with name, question count, flashcard count, threshold.

#### [NEW] `views/kms_quiz_views.xml`
- **Form** for `kms.quiz.question`: Question text, type selector, inline answer list with `is_correct` checkbox.
- **Tree** for `kms.quiz.attempt`: User, node, score, passed, date. Read-only.

#### [NEW] `views/kms_flashcard_views.xml`
- **Form**: Front (Html), Back (Html), parent node.
- **Tree**: Sequence-ordered list.

#### [NEW] `views/kms_milestone_views.xml`
- **Form** for `kms.milestone`: Name, description, course, instructor, linked nodes.
- **Form** for `kms.user.milestone`: Read-only learner info, submission files, state (statusbar widget), instructor feedback (Html), chatter at bottom (via `mail.thread`).

#### [NEW] `views/kms_learner_views.xml`
- Learner-facing views showing: enrolled courses, node progress (Kanban with state-colored cards), flashcard review queue (today's due cards), milestone submission forms.

#### [NEW] `views/kms_menus.xml`
Top-level app menu "KMS Mastery" with sub-menus:
- **Instructor**: Courses, Nodes, Milestones, Quiz Attempts (analytics)
- **Learner**: My Courses, My Progress, Flashcard Review, My Milestones

#### [NEW] `static/src/components/dag_viewer/`
Custom **OWL component** for interactive DAG visualization in the Odoo backend.
- Renders nodes as a force-directed or layered graph.
- Nodes are color-coded by user state: grey (locked), blue (unlocked), green (mastered).
- Click a node to navigate to its form view.
- Instructors can use it to visually inspect prerequisite chains.
- Registered in `web.assets_backend` via the manifest.

---

### Security (`security/`)

#### [NEW] `security/kms_security.xml`

Define two security groups under a new category:

```xml
<record id="module_category_kms" model="ir.module.category">
    <field name="name">KMS Mastery Learning</field>
</record>

<record id="group_kms_learner" model="res.groups">
    <field name="name">Learner</field>
    <field name="category_id" ref="module_category_kms"/>
</record>

<record id="group_kms_instructor" model="res.groups">
    <field name="name">Instructor</field>
    <field name="category_id" ref="module_category_kms"/>
    <field name="implied_ids" eval="[(4, ref('group_kms_learner'))]"/>
</record>
```

Record rules:
- **Learner own progress**: Learners can only read/write their own `kms.user.node`, `kms.user.flashcard`, `kms.user.milestone` records (`[('user_id', '=', user.id)]`).
- **Learner course enrollment**: Learners can only see `kms.course` records where they are in `learner_ids`.
- **Learner node access**: Learners can read all `kms.node` records (titles visible for DAG), but content fields are gated by computed field logic in the model.
- **Instructor**: Full access to all records in courses they instruct.

#### [NEW] `security/ir.model.access.csv`

| Model | Learner | Instructor |
|---|---|---|
| `kms.course` | R | CRUD |
| `kms.node` | R | CRUD |
| `kms.quiz.question` | R | CRUD |
| `kms.quiz.answer` | R | CRUD |
| `kms.quiz.attempt` | CR | R |
| `kms.quiz.attempt.line` | CR | R |
| `kms.flashcard` | R | CRUD |
| `kms.milestone` | R | CRUD |
| `kms.user.node` | CR | R |
| `kms.user.flashcard` | CRU | R |
| `kms.user.milestone` | CRU | CRUD |

---

### Automated Actions (`data/`)

#### [NEW] `data/mail_template_data.xml`

Mail template `kms_mastery.milestone_reminder_template`:
- **Subject**: "Reminder: Milestone '${object.milestone_id.name}' is awaiting evaluation"
- **Body**: Includes learner name, milestone name, submission date, link to the record.

#### [NEW] `data/ir_cron_data.xml`

```xml
<record id="ir_cron_milestone_reminder" model="ir.cron">
    <field name="name">KMS: Daily Milestone Evaluation Reminder</field>
    <field name="model_id" ref="model_kms_user_milestone"/>
    <field name="state">code</field>
    <field name="code">model._cron_send_milestone_reminders()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
    <field name="active" eval="True"/>
</record>
```

The `_cron_send_milestone_reminders()` method on `kms.user.milestone`:
1. Searches for records in `state='submitted'`.
2. For each, sends the mail template to both `user_id.partner_id` and `milestone_id.instructor_id.partner_id`.

---

### Demo Data (`demo/`)

#### [NEW] `demo/kms_demo_data.xml`

A sample curriculum for immediate testing after install:
- **1 Course**: "Python Fundamentals"
- **5 Nodes**: Variables → Data Types → Control Flow → Functions → Modules (linear DAG chain)
- **2–3 Quiz Questions per Node** with answers
- **2 Flashcards per Node**
- **1 Milestone**: "Build a CLI Calculator" (requires Functions + Control Flow)
- **1 Demo Instructor** and **1 Demo Learner** user

---

## Verification Plan

### Automated Tests

#### `tests/test_dag_logic.py`
- Verify `_has_cycle` constraint: creating A→B→C is OK; adding C→A raises `ValidationError`.
- Verify self-referential prerequisite (A→A) is rejected.
- Verify removing a prerequisite link works without error.

#### `tests/test_mastery_logic.py`
- Create nodes A→B. Verify B starts as `locked` for a new learner.
- Submit a passing quiz for A. Verify A becomes `mastered` and B transitions to `unlocked`.
- Submit a failing quiz for A. Verify A stays `unlocked`.
- Verify `kms.user.flashcard` records are auto-created when a node is mastered.
- Verify quiz attempt history is recorded.

#### `tests/test_fsrs_logic.py`
- Unit test `utils/fsrs.py` independently (no Odoo env needed).
- Test that `schedule()` with rating=Good increases stability.
- Test that `schedule()` with rating=Again triggers relearning state and resets stability.
- Test `compute_retrievability()` returns ~0.9 when elapsed_days equals stability.

### Manual Verification
1. Install the module on a fresh database.
2. Verify demo data creates the sample curriculum automatically.
3. Log in as the demo instructor — verify course, node, quiz, and milestone management views work.
4. Log in as the demo learner — verify only enrolled course is visible.
5. Attempt quiz on Node A with wrong answers — verify failure and attempt is recorded.
6. Attempt quiz on Node A with correct answers — verify mastery, Node B unlocks, flashcards appear.
7. Review a flashcard — verify FSRS state updates and next review date is computed.
8. Submit a milestone — verify chatter message, state change, and instructor receives reminder email next day.
9. Grade the milestone as instructor — verify reminders stop.
10. Verify the OWL DAG viewer renders nodes with correct color coding.
