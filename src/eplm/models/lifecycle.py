"""Lifecycle phase definitions and allowed transitions for electronics PLM."""

import enum


class LifecyclePhase(str, enum.Enum):
    """Phases an electronics product moves through during its lifecycle.

    Typical flow:
        CONCEPT -> DESIGN -> PROTOTYPE -> VALIDATION -> PRE_PRODUCTION
        -> PRODUCTION -> ACTIVE -> END_OF_LIFE -> OBSOLETE
    """

    CONCEPT = "concept"
    DESIGN = "design"
    PROTOTYPE = "prototype"
    VALIDATION = "validation"
    PRE_PRODUCTION = "pre_production"
    PRODUCTION = "production"
    ACTIVE = "active"
    END_OF_LIFE = "end_of_life"
    OBSOLETE = "obsolete"
    CANCELLED = "cancelled"


# Directed graph of valid phase transitions.
PHASE_TRANSITIONS: dict[LifecyclePhase, set[LifecyclePhase]] = {
    LifecyclePhase.CONCEPT: {LifecyclePhase.DESIGN, LifecyclePhase.CANCELLED},
    LifecyclePhase.DESIGN: {LifecyclePhase.PROTOTYPE, LifecyclePhase.CONCEPT, LifecyclePhase.CANCELLED},
    LifecyclePhase.PROTOTYPE: {LifecyclePhase.VALIDATION, LifecyclePhase.DESIGN, LifecyclePhase.CANCELLED},
    LifecyclePhase.VALIDATION: {LifecyclePhase.PRE_PRODUCTION, LifecyclePhase.PROTOTYPE, LifecyclePhase.CANCELLED},
    LifecyclePhase.PRE_PRODUCTION: {LifecyclePhase.PRODUCTION, LifecyclePhase.VALIDATION, LifecyclePhase.CANCELLED},
    LifecyclePhase.PRODUCTION: {LifecyclePhase.ACTIVE},
    LifecyclePhase.ACTIVE: {LifecyclePhase.END_OF_LIFE},
    LifecyclePhase.END_OF_LIFE: {LifecyclePhase.OBSOLETE},
    LifecyclePhase.OBSOLETE: set(),
    LifecyclePhase.CANCELLED: set(),
}


def can_transition(current: LifecyclePhase, target: LifecyclePhase) -> bool:
    """Return True if transitioning from *current* to *target* is allowed."""
    return target in PHASE_TRANSITIONS.get(current, set())
