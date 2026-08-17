# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

"""
Unit tests for the FSRS-5 scheduling algorithm.
These tests run independently of the Odoo environment.
"""

import unittest

from odoo.addons.kms_mastery.utils.fsrs import (
    CardState,
    Rating,
    State,
    compute_retrievability,
    init_card,
    schedule,
)


class TestFSRSLogic(unittest.TestCase):
    """Test the FSRS-5 scheduling algorithm."""

    def test_init_card(self):
        """init_card should return a default new card state."""
        card = init_card()
        self.assertEqual(card.state, State.NEW)
        self.assertEqual(card.difficulty, 5.0)
        self.assertEqual(card.stability, 0.0)
        self.assertEqual(card.reps, 0)
        self.assertEqual(card.lapses, 0)

    def test_retrievability_at_stability(self):
        """R should be ~0.9 when elapsed_days equals stability."""
        # R = (1 + t/(9*S))^-1
        # When t = S: R = (1 + 1/9)^-1 = (10/9)^-1 = 9/10 = 0.9
        r = compute_retrievability(stability=10.0, elapsed_days=10)
        self.assertAlmostEqual(r, 0.9, places=4)

    def test_retrievability_zero_stability(self):
        """R should be 0 when stability is 0."""
        r = compute_retrievability(stability=0.0, elapsed_days=5)
        self.assertEqual(r, 0.0)

    def test_retrievability_zero_elapsed(self):
        """R should be 1.0 when no time has elapsed."""
        r = compute_retrievability(stability=10.0, elapsed_days=0)
        self.assertAlmostEqual(r, 1.0, places=4)

    def test_retrievability_decreases_over_time(self):
        """R should decrease as more time elapses."""
        r1 = compute_retrievability(stability=10.0, elapsed_days=1)
        r2 = compute_retrievability(stability=10.0, elapsed_days=5)
        r3 = compute_retrievability(stability=10.0, elapsed_days=20)
        self.assertGreater(r1, r2)
        self.assertGreater(r2, r3)

    def test_schedule_new_card_good(self):
        """Scheduling a new card with Good should move to Learning."""
        card = init_card()
        new = schedule(card, Rating.GOOD, elapsed_days=0)
        self.assertEqual(new.state, State.LEARNING)
        self.assertGreater(new.stability, 0)
        self.assertGreater(new.difficulty, 0)
        self.assertEqual(new.reps, 1)

    def test_schedule_new_card_easy(self):
        """Scheduling a new card with Easy should move to Review."""
        card = init_card()
        new = schedule(card, Rating.EASY, elapsed_days=0)
        self.assertEqual(new.state, State.REVIEW)
        self.assertGreater(new.scheduled_days, 0)

    def test_schedule_good_increases_stability(self):
        """Rating Good on a review card should increase stability."""
        # Build a card that is in review state
        card = CardState(
            state=State.REVIEW,
            difficulty=5.0,
            stability=10.0,
            reps=5,
            lapses=0,
            elapsed_days=10,
            scheduled_days=10,
        )
        new = schedule(card, Rating.GOOD, elapsed_days=10)
        self.assertGreater(new.stability, card.stability)
        self.assertEqual(new.state, State.REVIEW)

    def test_schedule_again_triggers_relearning(self):
        """Rating Again on a review card should trigger relearning."""
        card = CardState(
            state=State.REVIEW,
            difficulty=5.0,
            stability=10.0,
            reps=5,
            lapses=0,
            elapsed_days=10,
            scheduled_days=10,
        )
        new = schedule(card, Rating.AGAIN, elapsed_days=10)
        self.assertEqual(new.state, State.RELEARNING)
        self.assertLessEqual(new.stability, card.stability)
        self.assertEqual(new.lapses, 1)

    def test_schedule_again_resets_stability(self):
        """Rating Again should reduce stability compared to the original."""
        card = CardState(
            state=State.REVIEW,
            difficulty=5.0,
            stability=20.0,
            reps=10,
            lapses=0,
            elapsed_days=20,
            scheduled_days=20,
        )
        new = schedule(card, Rating.AGAIN, elapsed_days=20)
        self.assertLess(new.stability, card.stability)

    def test_difficulty_clamped(self):
        """Difficulty should always stay in [1, 10]."""
        card = init_card()
        # Many easy ratings should not push difficulty below 1
        for _ in range(20):
            card = schedule(card, Rating.EASY, elapsed_days=1)
        self.assertGreaterEqual(card.difficulty, 1.0)

        # Many again ratings should not push difficulty above 10
        card = init_card()
        for _ in range(20):
            card = schedule(card, Rating.AGAIN, elapsed_days=0)
        self.assertLessEqual(card.difficulty, 10.0)

    def test_reps_increment(self):
        """Each review should increment the reps counter."""
        card = init_card()
        card = schedule(card, Rating.GOOD, elapsed_days=0)
        self.assertEqual(card.reps, 1)
        card = schedule(card, Rating.GOOD, elapsed_days=1)
        self.assertEqual(card.reps, 2)
        card = schedule(card, Rating.GOOD, elapsed_days=1)
        self.assertEqual(card.reps, 3)

    def test_lapses_increment_on_again(self):
        """Lapses should increment when rating Again from New state."""
        card = init_card()
        new = schedule(card, Rating.AGAIN, elapsed_days=0)
        self.assertEqual(new.lapses, 1)


if __name__ == '__main__':
    unittest.main()
