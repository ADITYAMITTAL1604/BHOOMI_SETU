# BhoomiSetu — Multi-Level Approval Workflow Definition

## Role Hierarchy (Top → Bottom Authority)

```
ADMIN / CENTRAL
    ↓ (system oversight, can override)
STATE (State Nodal Officer)
    ↓ approves
DISTRICT (District Land Acquisition Officer / Collector)
    ↓ approves
PROJECT_AGENCY (Project Authority — NHAI, Railways, etc.)
    ↓ initiates / monitors
FIELD_OFFICER (Tehsildar / Field Surveyor)
    ↓ submits
```

## Document Approval Chain

```
Field Officer
    ↓ submits document (Survey Report, Award, Objection, etc.)
Tehsildar (FIELD_OFFICER — senior)
    ↓ reviews and approves / rejects / requests revision
District Land Acquisition Officer (DISTRICT)
    ↓ approves / rejects / requests revision
State Nodal Officer (STATE)
    ↓ approves / rejects / requests revision
Project Authority (PROJECT_AGENCY)
    ↓ final approval — triggers stage progression

System Updates Acquisition Stage
    ← Only after full approval chain completes
```

## Approval Actions

| Action             | Code              | Description                                              |
|--------------------|-------------------|----------------------------------------------------------|
| Approve            | `APPROVED`        | Approver accepts the document/stage submission            |
| Reject             | `REJECTED`        | Approver rejects with mandatory remarks                  |
| Request Revision   | `REVISION_REQUESTED` | Approver sends back for correction with remarks       |

## Approval Record Schema

Each approval step stores:

| Field            | Type     | Description                          |
|------------------|----------|--------------------------------------|
| `approval_id`    | UUID     | Primary key                          |
| `document_id`    | UUID FK  | Document being approved              |
| `approver_id`    | UUID FK  | User who took action                 |
| `approver_role`  | String   | Role at time of action               |
| `action`         | Enum     | APPROVED / REJECTED / REVISION_REQUESTED |
| `remarks`        | Text     | Mandatory for reject/revision        |
| `step_order`     | Integer  | Position in approval chain (1,2,3,4) |
| `created_at`     | DateTime | Timestamp of action                  |

## Business Rules

1. Documents uploaded by FIELD_OFFICER start at step 1 (Tehsildar review).
2. Each step must complete before the next step becomes active.
3. A rejection at any step sends the document back to the submitter.
4. A revision request sends the document back to the submitter for correction.
5. Only after the final approval step (Project Authority) does the system update the acquisition stage.
6. ADMIN and CENTRAL roles can bypass the chain and directly approve.
7. Every approval action generates an audit log entry.
8. Pending approvals are visible on the approver's dashboard.

## Document Statuses

| Status               | Description                                    |
|----------------------|------------------------------------------------|
| `PENDING_REVIEW`     | Awaiting first-level review                    |
| `UNDER_REVIEW`       | Currently being reviewed at some level          |
| `REVISION_REQUESTED` | Sent back for correction                       |
| `REJECTED`           | Rejected — cannot proceed                      |
| `APPROVED`           | Fully approved through all levels              |

## Stage Impact Rules

- Document status `APPROVED` → System may trigger stage transition
- Document status `REJECTED` → No stage change; alert sent to submitter
- Document status `REVISION_REQUESTED` → No stage change; alert sent to submitter
- Document status `PENDING_REVIEW` or `UNDER_REVIEW` → Stage remains frozen
