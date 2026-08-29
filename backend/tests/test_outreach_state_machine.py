import pytest
from app.models.outreach import OutreachStatus
from app.services.outreach import (
    InvalidOutreachTransitionError,
    legal_next_statuses,
    validate_transition,
)

ALL_STATUSES = list(OutreachStatus)

LEGAL_TRANSITIONS = [
    (OutreachStatus.NOT_CONTACTED, OutreachStatus.IN_PROGRESS),
    (OutreachStatus.IN_PROGRESS, OutreachStatus.RESOLVED),
]

ILLEGAL_TRANSITIONS = [
    (current, requested)
    for current in ALL_STATUSES
    for requested in ALL_STATUSES
    if (current, requested) not in LEGAL_TRANSITIONS
]


@pytest.mark.parametrize(("current", "requested"), LEGAL_TRANSITIONS)
def test_legal_transitions_are_accepted(current: OutreachStatus, requested: OutreachStatus) -> None:
    validate_transition(current, requested)  # should not raise


@pytest.mark.parametrize(("current", "requested"), ILLEGAL_TRANSITIONS)
def test_illegal_transitions_are_rejected(
    current: OutreachStatus, requested: OutreachStatus
) -> None:
    with pytest.raises(InvalidOutreachTransitionError) as exc_info:
        validate_transition(current, requested)

    assert exc_info.value.current == current
    assert exc_info.value.requested == requested
    assert current.value in str(exc_info.value)
    assert requested.value in str(exc_info.value)


def test_not_contacted_cannot_jump_straight_to_resolved() -> None:
    with pytest.raises(InvalidOutreachTransitionError):
        validate_transition(OutreachStatus.NOT_CONTACTED, OutreachStatus.RESOLVED)


def test_resolved_is_terminal() -> None:
    assert legal_next_statuses(OutreachStatus.RESOLVED) == frozenset()


def test_same_status_transition_is_illegal() -> None:
    for status in ALL_STATUSES:
        with pytest.raises(InvalidOutreachTransitionError):
            validate_transition(status, status)


def test_legal_next_statuses_matches_transition_table() -> None:
    assert legal_next_statuses(OutreachStatus.NOT_CONTACTED) == frozenset(
        {OutreachStatus.IN_PROGRESS}
    )
    assert legal_next_statuses(OutreachStatus.IN_PROGRESS) == frozenset({OutreachStatus.RESOLVED})
