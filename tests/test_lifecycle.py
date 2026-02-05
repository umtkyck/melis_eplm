"""Tests for lifecycle phase transitions."""

import pytest

from eplm.models.lifecycle import LifecyclePhase, can_transition


class TestLifecycleTransitions:
    def test_concept_to_design_allowed(self):
        assert can_transition(LifecyclePhase.CONCEPT, LifecyclePhase.DESIGN) is True

    def test_concept_to_production_blocked(self):
        assert can_transition(LifecyclePhase.CONCEPT, LifecyclePhase.PRODUCTION) is False

    def test_design_to_prototype_allowed(self):
        assert can_transition(LifecyclePhase.DESIGN, LifecyclePhase.PROTOTYPE) is True

    def test_design_back_to_concept_allowed(self):
        assert can_transition(LifecyclePhase.DESIGN, LifecyclePhase.CONCEPT) is True

    def test_production_to_active_allowed(self):
        assert can_transition(LifecyclePhase.PRODUCTION, LifecyclePhase.ACTIVE) is True

    def test_active_to_end_of_life_allowed(self):
        assert can_transition(LifecyclePhase.ACTIVE, LifecyclePhase.END_OF_LIFE) is True

    def test_obsolete_terminal(self):
        for phase in LifecyclePhase:
            assert can_transition(LifecyclePhase.OBSOLETE, phase) is False

    def test_cancelled_terminal(self):
        for phase in LifecyclePhase:
            assert can_transition(LifecyclePhase.CANCELLED, phase) is False

    def test_early_phases_can_cancel(self):
        cancellable = [
            LifecyclePhase.CONCEPT,
            LifecyclePhase.DESIGN,
            LifecyclePhase.PROTOTYPE,
            LifecyclePhase.VALIDATION,
            LifecyclePhase.PRE_PRODUCTION,
        ]
        for phase in cancellable:
            assert can_transition(phase, LifecyclePhase.CANCELLED) is True

    def test_full_forward_path(self):
        path = [
            LifecyclePhase.CONCEPT,
            LifecyclePhase.DESIGN,
            LifecyclePhase.PROTOTYPE,
            LifecyclePhase.VALIDATION,
            LifecyclePhase.PRE_PRODUCTION,
            LifecyclePhase.PRODUCTION,
            LifecyclePhase.ACTIVE,
            LifecyclePhase.END_OF_LIFE,
            LifecyclePhase.OBSOLETE,
        ]
        for i in range(len(path) - 1):
            assert can_transition(path[i], path[i + 1]) is True, (
                f"Expected {path[i].value} -> {path[i+1].value} to be allowed"
            )
