"""Workflow engine for document lifecycle management.

State machine:
    gautas -> perziurimas -> patvirtintas
                          -> atmestas

Transitions are validated, logged, and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.models import Document, WorkflowStep

# --- Allowed transitions ---

TRANSITIONS: dict[str, list[str]] = {
    "gautas": ["perziurimas"],
    "perziurimas": ["patvirtintas", "atmestas"],
    "patvirtintas": [],
    "atmestas": ["perziurimas"],  # allow re-review
}

STATUS_LABELS: dict[str, str] = {
    "gautas": "Gautas",
    "perziurimas": "Perziurimas",
    "patvirtintas": "Patvirtintas",
    "atmestas": "Atmestas",
}

ALL_STATUSES = list(STATUS_LABELS.keys())


@dataclass
class TransitionResult:
    success: bool
    message: str
    step: WorkflowStep | None = None


def get_allowed_transitions(status: str) -> list[str]:
    """Return the list of statuses a document can move to from the given status."""
    return TRANSITIONS.get(status, [])


def transition_document(
    db: Session,
    document_id: int,
    to_status: str,
    actor: str,
    comment: str | None = None,
) -> TransitionResult:
    """Move a document to a new status with validation and audit logging.

    Args:
        db: SQLAlchemy session.
        document_id: ID of the document to transition.
        to_status: Target status.
        actor: Name or identifier of the person performing the action.
        comment: Optional comment explaining the transition.

    Returns:
        TransitionResult with success flag and message.
    """
    doc = db.get(Document, document_id)
    if doc is None:
        return TransitionResult(success=False, message=f"Dokumentas #{document_id} nerastas.")

    from_status = doc.status
    allowed = get_allowed_transitions(from_status)

    if to_status not in allowed:
        allowed_labels = ", ".join(STATUS_LABELS.get(s, s) for s in allowed) or "nera"
        return TransitionResult(
            success=False,
            message=(
                f"Negalima pereiti is '{STATUS_LABELS.get(from_status, from_status)}' "
                f"i '{STATUS_LABELS.get(to_status, to_status)}'. "
                f"Galimi pereijimai: {allowed_labels}."
            ),
        )

    # Apply transition
    doc.status = to_status
    doc.updated_at = datetime.now(timezone.utc)

    step = WorkflowStep(
        document_id=document_id,
        from_status=from_status,
        to_status=to_status,
        actor=actor,
        comment=comment,
        created_at=datetime.now(timezone.utc),
    )
    db.add(step)
    db.commit()
    db.refresh(step)

    return TransitionResult(
        success=True,
        message=f"Dokumentas perkeltas: {STATUS_LABELS.get(from_status)} -> {STATUS_LABELS.get(to_status)}.",
        step=step,
    )


def get_audit_trail(db: Session, document_id: int) -> list[WorkflowStep]:
    """Return the full audit trail for a document, ordered chronologically."""
    return (
        db.query(WorkflowStep)
        .filter(WorkflowStep.document_id == document_id)
        .order_by(WorkflowStep.created_at)
        .all()
    )


def get_status_counts(db: Session) -> dict[str, int]:
    """Return document counts grouped by status."""
    from sqlalchemy import func

    rows = db.query(Document.status, func.count(Document.id)).group_by(Document.status).all()
    counts = {s: 0 for s in ALL_STATUSES}
    for status, count in rows:
        counts[status] = count
    return counts


def get_type_status_matrix(db: Session) -> list[dict]:
    """Return a matrix of document counts by type and status."""
    from sqlalchemy import func

    from src.models import DocumentType

    rows = (
        db.query(DocumentType.name, Document.status, func.count(Document.id))
        .join(Document, Document.doc_type_id == DocumentType.id)
        .group_by(DocumentType.name, Document.status)
        .all()
    )

    matrix: dict[str, dict[str, int]] = {}
    for type_name, status, count in rows:
        if type_name not in matrix:
            matrix[type_name] = {s: 0 for s in ALL_STATUSES}
        matrix[type_name][status] = count

    return [{"type": name, **counts} for name, counts in sorted(matrix.items())]
