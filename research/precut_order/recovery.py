"""Single-instance recovery model, not a network consensus implementation.

Inputs stand for authenticated messages for one fixed committee and an authorized
leader/view. Values stand for fully validated and retrievable dependency records.
Election, signatures, record validation, durable I/O, and liveness are not modeled.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class Reply:
    instance: str
    target_view: int
    sender: int
    accepted: str | None


def recovery_choice(instance, view, replies, faults):
    n, q = 5 * faults + 1, 4 * faults + 1
    if (faults < 0 or view <= 0 or len(replies) != q
            or len({r.sender for r in replies}) != q
            or any(r.instance != instance or r.target_view != view
                   or r.sender not in range(n) for r in replies)):
        raise ValueError("invalid recovery certificate context or membership")
    counts = Counter(r.accepted for r in replies if r.accepted is not None)
    return next((value for value, count in counts.items() if count >= 2 * faults + 1), None)


class Replica:
    def __init__(self, instance, identity, faults, valid_values):
        self.instance = instance
        self.identity = identity
        self.faults = faults
        self.valid_values = frozenset(valid_values)
        self.view = 0
        self.accepted = None
        self.voted_view = -1
        self.replies = {}

    def query(self, view):
        if view <= 0 or view < self.view:
            raise ValueError("recovery view must be positive and not stale")
        self.view = view
        if view not in self.replies:
            self.replies[view] = Reply(self.instance, view, self.identity, self.accepted)
        return self.replies[view]

    def accept(self, view, value, certificate=()):
        if view < self.view or value not in self.valid_values:
            return False
        if self.voted_view == view:
            return value == self.accepted
        if view > 0:
            required = recovery_choice(self.instance, view, certificate, self.faults)
            if required is not None and required != value:
                return False
        self.view, self.voted_view, self.accepted = view, view, value
        return True
