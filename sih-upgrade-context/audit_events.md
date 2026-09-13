# BhoomiSetu — Audit Events Definition

## Tracked Events

| # | Event                    | Action Code                   | Entity Type | Tracked Fields                      |
|---|--------------------------|-------------------------------|-------------|--------------------------------------|
| 1 | Document Uploaded        | `DOCUMENT_UPLOADED`           | document    | document_type, title, file info      |
| 2 | Document Approved        | `DOCUMENT_APPROVED`           | document    | approver, step, remarks              |
| 3 | Document Rejected        | `DOCUMENT_REJECTED`           | document    | approver, step, rejection reason     |
| 4 | Document Revised         | `DOCUMENT_REVISED`            | document    | revision notes, new version          |
| 5 | Stage Changed            | `STAGE_TRANSITION`            | parcel      | old_stage → new_stage                |
| 6 | Compensation Released    | `COMPENSATION_RELEASED`       | compensation| amount, payment method               |
| 7 | Compensation Updated     | `COMPENSATION_UPDATED`        | compensation| old_amount → new_amount              |
| 8 | Possession Completed     | `POSSESSION_COMPLETED`        | parcel      | possession_date, mutation_ref        |
| 9 | Officer Reassigned       | `OFFICER_REASSIGNED`          | parcel      | old_officer → new_officer            |
| 10| Parcel Created           | `PARCEL_CREATED`              | parcel      | survey_number, area, location        |
| 11| Parcel Status Changed    | `PARCEL_STATUS_CHANGED`       | parcel      | old_status → new_status              |
| 12| Project Created          | `PROJECT_CREATED`             | project     | name, type, states                   |
| 13| Project Status Changed   | `PROJECT_STATUS_CHANGED`      | project     | old_status → new_status              |
| 14| SLA Breach Auto-Block    | `SLA_BREACH_AUTO_BLOCK`       | parcel      | stage, days_overdue                  |
| 15| User Login               | `USER_LOGIN`                  | user        | ip_address, user_agent               |
| 16| User Role Changed        | `USER_ROLE_CHANGED`           | user        | old_role → new_role                  |
| 17| Approval Chain Initiated | `APPROVAL_INITIATED`          | document    | document_type, first_approver        |
| 18| Approval Chain Completed | `APPROVAL_COMPLETED`          | document    | total_steps, final_status            |
| 19| R&R Record Updated       | `RR_RECORD_UPDATED`           | rr_record   | old_status → new_status              |

## Audit Log Record Schema

Each audit event contains:

| Field            | Type     | Description                          |
|------------------|----------|--------------------------------------|
| `log_id`         | UUID     | Unique log entry ID                  |
| `user_id`        | UUID FK  | Actor who performed the action       |
| `action`         | String   | Action code (see table above)        |
| `entity_type`    | String   | Type of entity affected              |
| `entity_id`      | UUID     | ID of affected entity                |
| `old_values`     | JSON     | Previous state (before change)       |
| `new_values`     | JSON     | New state (after change)             |
| `ip_address`     | String   | Client IP address                    |
| `user_agent`     | String   | Client user agent                    |
| `created_at`     | DateTime | Immutable timestamp                  |

## Timeline UI Requirements

The audit trail should render as a vertical timeline:

```
┌─────────────────────────────────────────────────────────┐
│  📋 Audit Trail — Parcel SN/MH/PUN/001                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ● 12 Sept 2026, 10:30 AM                              │
│  │  📄 Survey Report Uploaded                           │
│  │  by: field_user (Field Officer)                      │
│  │                                                      │
│  ● 13 Sept 2026, 02:15 PM                              │
│  │  ✅ Approved by Tehsildar                            │
│  │  by: tehsildar_user (District Officer)               │
│  │  Remarks: "Survey data verified and accurate"        │
│  │                                                      │
│  ● 15 Sept 2026, 11:00 AM                              │
│  │  💰 Compensation Released                            │
│  │  Amount: ₹12,50,000                                  │
│  │  by: district_user (District Officer)                │
│  │                                                      │
│  ● 18 Sept 2026, 04:30 PM                              │
│  │  🏠 Possession Completed                             │
│  │  by: field_user (Field Officer)                      │
│  │  Mutation Reference: MUT/PUN/2026/0891               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Search & Filter Capabilities

- Filter by entity_type
- Filter by action code
- Filter by user / actor
- Filter by date range
- Full-text search across remarks and values
- Export filtered audit logs

## Existing Infrastructure

The current `audit_logs` table and `AuditLog` model already support this schema.
The existing `/api/v1/audit-log` router provides admin-only listing.
Enhancement needed: role-scoped access, timeline UI, and richer event tracking.
