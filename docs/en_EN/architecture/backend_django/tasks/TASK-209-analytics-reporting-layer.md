# TASK-209: Analytics & Reporting Layer (Admin Cabinet)

[⬅️ Back to Roadmap](../roadmap.md)

## 🎯 Goal
Implement the backend and frontend components for the Analytics section in the Admin Cabinet.

## 📋 Requirements

### 1. Backend (Selectors & Logic)
- [ ] **`get_revenue_stats(start_date, end_date)`**: Calculate total revenue and breakdown by master.
- [ ] **`get_appointment_stats()`**: Count completed, cancelled, and pending appointments.
- [ ] **`get_service_popularity()`**: Rank services by volume and revenue.

### 2. Frontend (Cabinet UI)
- [ ] **New View:** `AnalyticsView` in `features/cabinet/views/analytics.py`.
- [ ] **Template:** `templates/cabinet/analytics/index.html`.
- [ ] **Charts:** Integrate a lightweight charting library (e.g., Chart.js) to visualize revenue trends.
- [ ] **Filters:** Add a date range picker to filter all stats.

### 3. Navigation
- [ ] Add "Analytics" link to the Cabinet sidebar.

## 🔗 Global Task Reference
Part of [TASK-GLOBAL-007: CRM Analytics & Reporting System](../../../global_task/TASK-GLOBAL-007-analytics-system.md)
