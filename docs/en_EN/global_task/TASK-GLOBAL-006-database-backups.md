# TASK-GLOBAL-006: Automated GDPR-Compliant Database Backups

## 🎯 Overview
Ensure data safety and **DSGVO (GDPR) compliance** by implementing daily automated, encrypted backups of the PostgreSQL database with storage on **Hetzner Storage Box (Germany)**.

---

## 🛡️ Security & Compliance (DSGVO)
- **Storage Location:** Hetzner Online GmbH (Germany).
- **Encryption:** Mandatory client-side encryption (AES-256) *before* the backup leaves the server.

---

## 🔄 The "Secure Backup" Flow (Step-by-Step)

1. **Dump:** `system-worker` runs `pg_dump` daily at 03:00 AM.
2. **Encryption:** Snapshot is compressed and encrypted using a master key.
3. **Storage:** Encrypted file is uploaded via SFTP/SCP to Hetzner.
4. **Notification:** Bot sends a status message (Success/Failure) to the Admin Telegram chat.

---

## 🏗️ Layer Responsibilities & Sub-Tasks

### 1. Worker Layer (System)
- [ ] **[TASK-WRK-105: Secure Backup Script](../../architecture/workers/system_worker/tasks/TASK-WRK-105-secure-backup.md)** (Note: Task file to be created when On Hold status is lifted).
- [ ] **SFTP Client:** Logic to transfer files to Hetzner.

### 2. Infrastructure Layer (Docker)
- [ ] **[TASK-INF-101: Backup Tools Integration](../../infrastructure/tasks/TASK-INF-101-backup-tools.md)** (Note: Task file to be created when On Hold status is lifted).
- [ ] **Worker Image:** Install `postgresql-client`, `openssl`, and `openssh-client`.

---

## 🔗 Status Tracking
- **Current Status:** ⏸️ On Hold (Waiting for business Telegram channel setup)
- **Next Milestone:** Setup Hetzner Storage Box and SSH keys.
