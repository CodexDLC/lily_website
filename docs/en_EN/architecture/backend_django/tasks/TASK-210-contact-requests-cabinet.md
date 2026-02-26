# TASK-210: Contact Requests Management (Admin Cabinet)

[⬅️ Back to Roadmap](../roadmap.md)

## 🎯 Goal
Integrate the "Contact Requests" (messages from the website form) into the Admin Cabinet, similar to how appointments are managed.

## 📋 Requirements

### 1. Backend (Selectors & Logic)
- [ ] **`get_contact_requests()`**: Fetch all messages from the `ContactRequest` model, ordered by date.
- [ ] **Status Management:** Add ability to mark requests as "Read" or "Processed".

### 2. Frontend (Cabinet UI)
- [ ] **New View:** `ContactRequestsView` in `features/cabinet/views/contacts.py`.
- [ ] **Template:** `templates/cabinet/contacts/list.html`.
- [ ] **UI Cards:** Display sender name, phone/email, message text, and timestamp.
- [ ] **HTMX Actions:** Buttons to mark as processed or delete.

### 3. Navigation
- [ ] Add "Messages" (or "Contact Requests") link to the Cabinet sidebar.
- [ ] **Badge:** Show the count of unread messages in the sidebar.

## 🔗 Global Task Reference
Part of [⚙️ Admin & Backend](../roadmap.md#-admin--backend)
