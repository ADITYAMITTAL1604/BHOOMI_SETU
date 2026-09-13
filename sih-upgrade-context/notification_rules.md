# BhoomiSetu — Notification Rules Definition

## Notification Triggers

| # | Trigger Event                | Condition                                | Severity   | Recipients                          |
|---|------------------------------|------------------------------------------|------------|-------------------------------------|
| 1 | Approval Pending > 3 Days   | Approval step pending ≥ 3 calendar days  | WARNING    | Current approver + immediate superior |
| 2 | Survey Pending > 7 Days     | SURVEY stage IN_PROGRESS ≥ 7 days        | WARNING    | Assigned field officer + district officer |
| 3 | Compensation Pending > 15 Days | Compensation payment_status=PENDING ≥ 15 days | WARNING | District officer + state officer |
| 4 | Stage SLA Breached           | Stage target_date < today                | CRITICAL   | Assigned officer + district + state |
| 5 | Document Rejected            | Approval action = REJECTED               | WARNING    | Document submitter                  |
| 6 | Document Approved            | Document fully approved (all steps)      | INFO       | Document submitter + project agency |
| 7 | Revision Requested           | Approval action = REVISION_REQUESTED     | INFO       | Document submitter                  |
| 8 | Stage Completed              | Stage status changed to COMPLETED        | INFO       | Assigned officer + next stage officer |
| 9 | Possession Completed         | POSSESSION stage marked COMPLETED        | INFO       | Project agency + state officer      |
| 10| Officer Reassigned           | assigned_officer field changed            | INFO       | Old officer + new officer           |
| 11| SLA Warning (7 days before)  | Days remaining ≤ warning_threshold_days  | WARNING    | Assigned officer                    |
| 12| New Document Uploaded        | Document created                          | INFO       | First-level approver (Tehsildar)    |

## Notification Channels

| Channel        | Status            | Implementation                           |
|---------------|-------------------|------------------------------------------|
| In-App Bell   | ✅ Implement Now   | Bell icon with unread counter in TopBar  |
| Email          | 🔲 Future Ready    | Architecture supports via provider interface |
| SMS            | 🔲 Future Ready    | Architecture supports via provider interface |
| Push           | 🔲 Future Ready    | Architecture supports via provider interface |

## Notification Data Schema

| Field            | Type     | Description                          |
|------------------|----------|--------------------------------------|
| `notification_id`| UUID     | Unique notification ID               |
| `user_id`        | UUID FK  | Recipient user                       |
| `title`          | String   | Short notification title             |
| `message`        | Text     | Detailed message body                |
| `severity`       | Enum     | INFO / WARNING / CRITICAL            |
| `category`       | String   | approval / sla / document / stage / system |
| `is_read`        | Boolean  | Read status                          |
| `read_at`        | DateTime | When marked as read                  |
| `entity_type`    | String   | parcel / project / document          |
| `entity_id`      | UUID     | Link to related entity               |
| `metadata_json`  | JSON     | Additional context data              |
| `created_at`     | DateTime | Notification timestamp               |

## UI Features

- **Bell Icon**: In TopBar with unread count badge
- **Dropdown Panel**: Shows latest 10 notifications
- **Full Page**: `/notifications` with filters and search
- **Mark Read**: Single notification or "Mark All Read"
- **Click Action**: Navigate to relevant entity (parcel, project, document)
- **Auto-refresh**: Poll every 30 seconds for new notifications

## Note

The existing `Alert` model (`alerts` table) already provides the base structure.
The notification system should extend/reuse the Alert infrastructure rather than creating a parallel system.
