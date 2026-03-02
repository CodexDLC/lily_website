# TASK-210: Contact Requests Management (Admin Cabinet)

[⬅️ Back to Roadmap](../roadmap.md)

## 🎯 Goal
Integrate the "Contact Requests" (messages from the website form) into the Admin Cabinet, similar to how appointments are managed.

## 📋 Requirements

### 1. Backend (Selectors & Logic)
- [x] **`get_contact_requests()`**: Fetch all messages from the `ContactRequest` model, ordered by date.
- [x] **Status Management:** Add ability to mark requests as "Read" or "Processed".

### 2. Frontend (Cabinet UI)
- [x] **New View:** `ContactRequestsView` in `features/cabinet/views/contacts.py`.
- [x] **Template:** `templates/cabinet/contacts/list.html`.
- [x] **UI Cards:** Display sender name, phone/email, message text, and timestamp.
- [x] **HTMX Actions:** Buttons to mark as processed or delete.

### 3. Navigation
- [x] Add "Messages" (or "Contact Requests") link to the Cabinet sidebar.
- [x] **Badge:** Show the count of unread messages in the sidebar.

## 🔗 Global Task Reference
Part of [⚙️ Admin & Backend](../roadmap.md#-admin--backend)
