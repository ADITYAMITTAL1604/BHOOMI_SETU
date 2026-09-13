# BhoomiSetu — Report Filters Definition

## Administrative Filters

| Filter       | Type       | Source                | Description                          |
|-------------|------------|------------------------|--------------------------------------|
| State       | Dropdown   | `parcels.state`        | Filter by state (multi-select)       |
| District    | Dropdown   | `parcels.district`     | Cascading from state selection       |
| Tehsil      | Dropdown   | `parcels.village`      | Sub-district unit (village-level)    |
| Village     | Dropdown   | `parcels.village`      | Specific village                     |

## Project Filters

| Filter          | Type       | Source              | Description                          |
|----------------|------------|----------------------|--------------------------------------|
| Project Type   | Dropdown   | `projects.type`      | Highway, Railway, Metro, Port, Industrial, Canal, Airport |
| Project Agency | Dropdown   | Derived from users   | NHAI, Railway Board, Metro Corp, etc. |
| Project Name   | Search     | `projects.name`      | Free-text search                     |
| Project Status | Dropdown   | `projects.status`    | PLANNING, ACTIVE, ON_HOLD, COMPLETED, CANCELLED |

## Acquisition Stage Filters

| Filter               | Type       | Source                      | Description                          |
|----------------------|------------|------------------------------|--------------------------------------|
| Current Stage        | Dropdown   | `parcels.current_stage`      | 11-stage acquisition workflow        |
| Stage Status         | Dropdown   | `acquisition_stages.status`  | NOT_STARTED, IN_PROGRESS, COMPLETED, BLOCKED, SKIPPED |

## Status Filters

| Filter               | Type       | Logic                        | Description                          |
|----------------------|------------|------------------------------|--------------------------------------|
| Delayed Projects     | Checkbox   | SLA breach count > 0         | Projects with breached SLA stages    |
| Compensation Pending | Checkbox   | payment_status = PENDING     | Parcels awaiting compensation        |
| Approvals Pending    | Checkbox   | approval_status = PENDING    | Documents awaiting approval          |
| Possession Pending   | Checkbox   | stage != CLOSURE/POSSESSION  | Parcels not yet possessed            |
| High Risk            | Checkbox   | risk_score > 0.7             | Parcels with high risk scores        |

## Date Range Filters

| Filter          | Type       | Description                          |
|----------------|------------|--------------------------------------|
| Last 7 Days    | Preset     | Created/updated in last 7 days       |
| Last 30 Days   | Preset     | Created/updated in last 30 days      |
| This Quarter   | Preset     | Current fiscal quarter               |
| Fiscal Year    | Preset     | Current fiscal year (Apr–Mar)        |
| Custom Range   | Date Picker| User-defined start and end dates     |

## KPI Metrics (Computed from filtered data)

| KPI                     | Calculation                              |
|------------------------|------------------------------------------|
| Total Land Required    | SUM(projects.land_required_ha)           |
| Total Land Acquired    | SUM(projects.land_acquired_ha)           |
| Acquisition Progress % | (acquired / required) × 100             |
| Compensation Released  | SUM(compensation.paid_amount)            |
| Compensation Pending   | SUM(approved_amount - paid_amount)       |
| Average Delay (Days)   | AVG(days_overdue) for breached stages    |
| Projects At Risk       | COUNT where risk_score > 0.7             |
| Pending Approvals      | COUNT where approval_status = PENDING    |
| SLA Breach Count       | COUNT stages past target_date            |
| Total Affected Families| COUNT(rr_records)                        |

## Export Formats

| Format      | Method                           | Description                    |
|------------|----------------------------------|--------------------------------|
| PDF        | Server-side HTML → PDF rendering | Government-style report        |
| Excel/CSV  | Server-side XLSX generation      | Data export for analysis       |
| HTML       | Printable HTML document          | Browser print-friendly         |
