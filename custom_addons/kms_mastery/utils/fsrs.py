"""
FSRS-5 (Free Spaced Repetition Scheduler) — Pure Python Implementation

Implements the DSR memory model (Difficulty, Stability, Retrievability)
based on the FSRS-5 algorithm. No Odoo dependencies so it can be
unit-tested independently.

Reference: https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm
"""

import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional


class Rating(IntEnum):
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


class State(IntEnum):
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


# Default FSRS-5 weights (w0–w18)
DEFAULT_WEIGHTS: List[float] = [
    0.4072,   # w0  - initial stability for Again
    1.1829,   # w1  - initial stability for Hard
    3.1262,   # w2  - initial stability for Good
    15.4722,  # w3  - initial stability for Easy
    7.2102,   # w4  - difficulty mean reversion
    0.5316,   # w5  - difficulty base
    1.0651,   # w6  - difficulty factor for Good
    0.0046,   # w7  - stability increase base
    1.5418,   # w8  - stability increase exponent (difficulty)
    0.1546,   # w9  - stability increase exponent (stability)
    1.0190,   # w10 - stability increase exponent (retrievability)
    1.9395,   # w11 - stability penalty for failure
    0.1100,   # w12 - stability recovery base after failure
    0.2960,   # w13 - stability recovery exponent (difficulty)
    2.2682,   # w14 - stability recovery exponent (stability)
    0.2307,   # w15 - hard penalty multiplier
    0.0009,   # w16 - easy bonus multiplier
    2.9466,   # w17 - short-term stability factor (for learning/relearning)
    0.5100,   # w18 - short-term stability exponent
]

DECAY = -0.5
FACTOR = 19 / 81  # (0.9 ^ (1/DECAY) - 1)


@dataclass
class CardState:
    """Represents the current state of a flashcard for FSRS scheduling."""
    state: int = State.NEW
    difficulty: float = 5.0
    stability: float = 0.0
    elapsed_days: int = 0
    scheduled_days: int = 0
    reps: int = 0
    lapses: int = 0


def compute_retrievability(stability: float, elapsed_days: int) -> float:
    """
    Compute the retrievability (probability of recall) using the FSRS
    forgetting curve formula:

        R = (1 + t / (9 * S)) ^ -1

    This is equivalent to:  R = (1 + FACTOR * t / S) ^ (1/DECAY)

    Args:
        stability: Current stability in days (S parameter)
        elapsed_days: Days since last review (t)

    Returns:
        Retrievability between 0.0 and 1.0. Returns 0.0 if stability is 0.
    """
    if stability <= 0:
        return 0.0
    return (1.0 + (elapsed_days / (9.0 * stability))) ** -1


def _clamp_difficulty(d: float) -> float:
    """Clamp difficulty to the valid range [1, 10]."""
    return max(1.0, min(10.0, d))


def _clamp_stability(s: float) -> float:
    """Ensure stability is at least a small positive value."""
    return max(0.01, s)


def _initial_stability(rating: int, weights: List[float]) -> float:
    """Compute initial stability for a new card based on first rating."""
    # w0–w3 are initial stabilities for Again/Hard/Good/Easy
    return max(0.01, weights[rating - 1])


def _initial_difficulty(rating: int, weights: List[float]) -> float:
    """Compute initial difficulty for a new card based on first rating."""
    # D0(G) = w4 - exp(w5 * (G - 1)) + 1
    d = weights[4] - math.exp(weights[5] * (rating - 1)) + 1
    return _clamp_difficulty(d)


def _next_difficulty(d: float, rating: int, weights: List[float]) -> float:
    """
    Compute the next difficulty after a review.

    Uses mean reversion towards w4:
        D'(D, G) = w7 * D0(3) + (1 - w7) * (D - w6 * (G - 3))

    where D0(3) is the initial difficulty for a Good rating.
    """
    d0_good = weights[4] - math.exp(weights[5] * (3 - 1)) + 1
    delta = d - weights[6] * (rating - 3)
    new_d = weights[7] * d0_good + (1 - weights[7]) * delta
    return _clamp_difficulty(new_d)


def _next_recall_stability(
    d: float, s: float, r: float, rating: int, weights: List[float]
) -> float:
    """
    Compute the new stability after a successful recall (rating >= Hard).

    S'_r(D, S, R, G) = S * (e^(w8) * (11 - D) * S^(-w9) * (e^(w10 * (1 - R)) - 1) * hard_penalty * easy_bonus + 1)
    """
    hard_penalty = weights[15] if rating == Rating.HARD else 1.0
    easy_bonus = (1.0 + weights[16]) if rating == Rating.EASY else 1.0

    new_s = s * (
        math.exp(weights[8])
        * (11.0 - d)
        * (s ** (-weights[9]))
        * (math.exp(weights[10] * (1.0 - r)) - 1.0)
        * hard_penalty
        * easy_bonus
        + 1.0
    )
    return _clamp_stability(new_s)


def _next_forget_stability(
    d: float, s: float, r: float, weights: List[float]
) -> float:
    """
    Compute the new stability after forgetting (rating = Again).

    S'_f(D, S, R) = w11 * D^(-w12) * ((S + 1)^w13 - 1) * e^(w14 * (1 - R))
    """
    new_s = (
        weights[11]
        * (d ** (-weights[12]))
        * ((s + 1.0) ** weights[13] - 1.0)
        * math.exp(weights[14] * (1.0 - r))
    )
    return _clamp_stability(min(new_s, s))  # S'_f should not exceed S


def _next_short_term_stability(
    s: float, rating: int, weights: List[float]
) -> float:
    """
    Compute stability for learning/relearning states.

    S'_s(S, G) = S * e^(w17 * (G - 3 + w18))
    """
    new_s = s * math.exp(weights[17] * (rating - 3 + weights[18]))
    return _clamp_stability(new_s)


def _next_interval(stability: float, desired_retention: float) -> int:
    """
    Compute the next review interval in days from stability and desired retention.

    I(r, S) = (S / FACTOR) * (r ^ (1/DECAY) - 1)

    Simplified: I = 9 * S * (1/r - 1) when DECAY = -0.5
    """
    if desired_retention <= 0 or desired_retention >= 1:
        desired_retention = 0.9

    interval = (9.0 * stability) * (1.0 / desired_retention - 1.0)
    return max(1, round(interval))


def init_card() -> CardState:
    """Return a new card state with default FSRS parameters."""
    return CardState()


def schedule(
    state: CardState,
    rating: int,
    elapsed_days: int,
    desired_retention: float = 0.9,
    weights: Optional[List[float]] = None,
) -> CardState:
    """
    Compute the next card state after a review.

    Args:
        state: Current card state
        rating: User's rating (1=Again, 2=Hard, 3=Good, 4=Easy)
        elapsed_days: Days since last review
        desired_retention: Target retention probability (default 0.9)
        weights: FSRS-5 weights (w0–w18). Uses defaults if None.

    Returns:
        New CardState with updated FSRS parameters
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    rating = max(1, min(4, rating))

    new = CardState(
        reps=state.reps + 1,
        lapses=state.lapses,
        elapsed_days=elapsed_days,
    )

    if state.state == State.NEW:
        # First review of a new card
        new.difficulty = _initial_difficulty(rating, weights)
        new.stability = _initial_stability(rating, weights)

        if rating == Rating.AGAIN:
            new.state = State.LEARNING
            new.scheduled_days = 0
            new.lapses = state.lapses + 1
        elif rating == Rating.HARD:
            new.state = State.LEARNING
            new.scheduled_days = 0
        elif rating == Rating.GOOD:
            new.state = State.LEARNING
            new.scheduled_days = 0
        else:  # EASY
            new.state = State.REVIEW
            interval = _next_interval(new.stability, desired_retention)
            new.scheduled_days = interval

    elif state.state == State.LEARNING or state.state == State.RELEARNING:
        # In learning or relearning: use short-term stability
        new.difficulty = _next_difficulty(state.difficulty, rating, weights)
        new.stability = _next_short_term_stability(
            state.stability, rating, weights
        )

        if rating == Rating.AGAIN:
            new.state = state.state  # Stay in same learning state
            new.scheduled_days = 0
            new.lapses = state.lapses + (
                1 if state.state == State.REVIEW else 0
            )
        elif rating in (Rating.HARD, Rating.GOOD):
            new.state = state.state
            new.scheduled_days = 0
        else:  # EASY
            new.state = State.REVIEW
            interval = _next_interval(new.stability, desired_retention)
            new.scheduled_days = interval

    else:  # State.REVIEW
        r = compute_retrievability(state.stability, elapsed_days)
        new.difficulty = _next_difficulty(state.difficulty, rating, weights)

        if rating == Rating.AGAIN:
            new.stability = _next_forget_stability(
                new.difficulty, state.stability, r, weights
            )
            new.state = State.RELEARNING
            new.scheduled_days = 0
            new.lapses = state.lapses + 1
        else:
            new.stability = _next_recall_stability(
                new.difficulty, state.stability, r, rating, weights
            )
            new.state = State.REVIEW
            interval = _next_interval(new.stability, desired_retention)
            new.scheduled_days = interval

    return new
