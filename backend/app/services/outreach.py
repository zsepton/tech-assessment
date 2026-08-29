"""Outreach status state machine.

Legal transitions form a strict linear progression:

    NOT_CONTACTED -> IN_PROGRESS -> RESOLVED

RESOLVED is terminal — no reopen/back-transition is modeled, since nothing
in the assessment calls for revisiting a resolved case, and adding one
un-asked-for would be scope beyond what's needed.

A same-status "transition" (e.g. IN_PROGRESS -> IN_PROGRESS) is deliberately
NOT considered legal here: the transition table below defines the exact set
of moves this state machine allows, and stalling in place isn't one of them.
"""

from app.models.outreach import OutreachStatus

OUTREACH_TRANSITIONS: dict[OutreachStatus, frozenset[OutreachStatus]] = {
    OutreachStatus.NOT_CONTACTED: frozenset({OutreachStatus.IN_PROGRESS}),
    OutreachStatus.IN_PROGRESS: frozenset({OutreachStatus.RESOLVED}),
    OutreachStatus.RESOLVED: frozenset(),
}


class InvalidOutreachTransitionError(ValueError):
    """Raised when a requested outreach status transition isn't legal."""

    def __init__(self, current: OutreachStatus, requested: OutreachStatus) -> None:
        self.current = current
        self.requested = requested
        super().__init__(
            f"Cannot transition outreach status from {current.value} to {requested.value}."
        )


def legal_next_statuses(current: OutreachStatus) -> frozenset[OutreachStatus]:
    """The set of statuses `current` may legally transition to."""
    return OUTREACH_TRANSITIONS[current]


def validate_transition(current: OutreachStatus, requested: OutreachStatus) -> None:
    """Raise InvalidOutreachTransitionError unless `requested` is a legal next status."""
    if requested not in legal_next_statuses(current):
        raise InvalidOutreachTransitionError(current, requested)
