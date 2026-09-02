"""BhoomiSetu — Domain Enumerations (TRD §3.3)."""

from enum import Enum


class UserRole(str, Enum):
    """User roles per TRD §3.3 / Security §2.2."""
    ADMIN = "ADMIN"
    CENTRAL = "CENTRAL"
    STATE = "STATE"
    DISTRICT = "DISTRICT"
    PROJECT_AGENCY = "PROJECT_AGENCY"
    FIELD_OFFICER = "FIELD_OFFICER"


class ProjectStatus(str, Enum):
    """Lifecycle status of an infrastructure project."""
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class StageName(str, Enum):
    """Standard 11-stage land acquisition workflow per TRD §3.3."""
    PROPOSAL = "PROPOSAL"
    IDENTIFICATION = "IDENTIFICATION"
    SURVEY = "SURVEY"
    VERIFICATION = "VERIFICATION"
    NOTIFICATION = "NOTIFICATION"
    OBJECTION = "OBJECTION"
    AWARD = "AWARD"
    COMPENSATION = "COMPENSATION"
    REHABILITATION_RESETTLEMENT = "REHABILITATION_RESETTLEMENT"
    POSSESSION = "POSSESSION"
    CLOSURE = "CLOSURE"


class ParcelStatus(str, Enum):
    """Status of an individual land parcel."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"


class StageStatus(str, Enum):
    """Status of an individual acquisition stage execution."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class CompensationPaymentStatus(str, Enum):
    """Payment status for land compensation disbursements."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    DISBURSED = "DISBURSED"
    DISPUTED = "DISPUTED"


class AffectedType(str, Enum):
    """Type of Project Affected Family (PAF) / Person (PAP)."""
    TITLE_HOLDER = "TITLE_HOLDER"
    TENANT = "TENANT"
    AGRICULTURAL_LABOURER = "AGRICULTURAL_LABOURER"
    COMMERCIAL_TENANT = "COMMERCIAL_TENANT"
    SQUATTER = "SQUATTER"


class RehabilitationStatus(str, Enum):
    """R&R process status."""
    IDENTIFIED = "IDENTIFIED"
    PLAN_APPROVED = "PLAN_APPROVED"
    ALLOTMENT_DONE = "ALLOTMENT_DONE"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"


class DocumentType(str, Enum):
    """Categories of official documents."""
    NOTIFICATION = "NOTIFICATION"
    SURVEY_REPORT = "SURVEY_REPORT"
    OWNERSHIP_RECORD = "OWNERSHIP_RECORD"
    AWARD_ORDER = "AWARD_ORDER"
    COMPENSATION_RECEIPT = "COMPENSATION_RECEIPT"
    RR_PLAN = "RR_PLAN"
    POSSESSION_ORDER = "POSSESSION_ORDER"
    MAP = "MAP"
    OTHER = "OTHER"


class AlertSeverity(str, Enum):
    """Notification / Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
