# KMS Mastery Learning

**KMS Mastery Learning** is an advanced Odoo 19 module designed for education and training. It implements a mastery-based Knowledge Management System (KMS) focusing on structured learning paths, active recall, and comprehensive evaluations.

## 🚀 Key Features

*   **Directed Acyclic Graph (DAG) for Knowledge Nodes:** Organize your courses into structured graphs of knowledge nodes. Define dependencies between nodes to enforce prerequisite completion, ensuring learners follow a structured learning path.
*   **Auto-Graded Quizzes:** Assess learner knowledge with auto-graded quizzes. Configure custom mastery thresholds required to pass and unlock subsequent knowledge nodes.
*   **FSRS Spaced-Repetition Flashcards:** Integrate modern Free Spaced Repetition Scheduler (FSRS) flashcards to promote long-term retention of critical concepts. Learners can review flashcards effectively using an optimized schedule.
*   **Human-Graded Milestones:** Incorporate subjective or practical assignments as milestones. These are graded by instructors, and the system sends daily reminder notifications for pending reviews.
*   **Interactive OWL Visualizations:** 
    *   **DAG Viewer:** A modern, interactive visualization component built with Odoo's OWL framework, allowing users to visually navigate course structures and their progress.
    *   **Flashcard Reviewer:** A dedicated, interactive OWL interface for studying and reviewing flashcards seamlessly within Odoo.

## 📦 Dependencies

This module depends on the following standard Odoo modules:
*   `base`
*   `mail` (for daily reminder notifications)
*   `web` (for OWL components and backend assets)

## 🛠️ Installation

1.  Place the `kms_mastery` module directory into your Odoo `custom_addons` path.
2.  Restart the Odoo server.
3.  Log in to Odoo as an Administrator.
4.  Navigate to **Apps**.
5.  Remove the `Apps` filter and search for `KMS Mastery Learning`.
6.  Click **Activate**.

## 📖 Usage & Configuration

### Security Roles
The module introduces specific access rights tailored for a learning environment (e.g., Instructors and Learners). Ensure you assign the appropriate KMS groups to your users via **Settings > Users & Companies > Users**.

### Setting Up a Course (DAG)
1.  Navigate to the **KMS** application.
2.  Create a new **Course**.
3.  Within the course, define **Knowledge Nodes**.
4.  For each node, set up its prerequisites by linking to other nodes, automatically building the DAG structure.

### Quizzes & Milestones
*   **Quizzes:** Add questions and answers to a node. Set the mastery threshold (e.g., 80%) required to mark the node as mastered.
*   **Milestones:** Define milestone assignments that require manual grading by an instructor before the learner can progress.

### Flashcards
*   Create flashcards associated with specific nodes. 
*   Learners will use the interactive Flashcard Review interface to study, and the FSRS algorithm will handle scheduling based on their performance.

## 💻 Technical Details
*   **Version:** 19.0.1.0.0
*   **Category:** Education
*   **License:** LGPL-3
*   **Author:** Antigravity

## 🛡️ Support
If you encounter any issues or have questions about configuring the DAG, FSRS flashcards, or OWL components, please reach out to the author or consult the technical documentation.
