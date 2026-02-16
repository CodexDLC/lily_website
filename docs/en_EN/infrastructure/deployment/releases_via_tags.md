# 🏷️ Tag-Based Production Releases

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

---

## 📋 Overview

This document describes the **tag-based release workflow** for deploying to production. Instead of merging to a long-lived `release` branch, we use **git tags** to trigger deployments.

### What Changed?

**Old Approach (via release branch):**
```bash
develop → main → release (PR) → deploy → reverse merge to main/develop 😖
```

**New Approach (via tags):**
```bash
develop → main (PR) → create tag v1.2.3 → automatic deploy 🚀
```

### Benefits:

✅ **No reverse merging** - eliminates back-merging `release` into `main` and `develop`
✅ **Clean history** - tags clearly mark released versions
✅ **Easy rollbacks** - revert to any version: `git checkout v1.2.2`
✅ **Fewer branches** - only `develop` and `main`, no `release`
✅ **Faster releases** - simplified workflow reduces manual steps

---

## 🚀 How to Release: Step-by-Step Guide

### Step 1: Verify develop branch

Ensure all features ready for release are in `develop`:

```bash
git checkout develop
git pull origin develop
git log --oneline -10  # View last 10 commits
```

### Step 2: Run local checks

Before merging to `main`, **always** run local validation:

```bash
.\tools\dev\check_local.ps1  # Windows
# or
pwsh tools/dev/check_local.ps1  # Linux/Mac
```

Must pass:
- ✅ Ruff format (code formatting)
- ✅ Ruff lint (style checks)
- ✅ Mypy (type checking)
- ✅ Pytest unit tests

### Step 3: Merge develop → main

Open Pull Request from `develop` to `main` on GitHub:

```bash
# On GitHub:
# 1. Go to "Pull requests"
# 2. Click "New pull request"
# 3. base: main ← compare: develop
# 4. Fill in PR description
# 5. Click "Create pull request"
```

**GitHub Actions will automatically run:**
- 🧪 Full test suite (including integration tests)
- 🐳 Docker build verification

**Only merge PR after CI passes successfully!**

### Step 4: Create release tag

After PR is merged to `main`, create a tag:

```bash
# 1. Switch to main and pull latest changes
git checkout main
git pull origin main

# 2. Create annotated tag (format: v1.2.3)
git tag -a v1.2.3 -m "Release 1.2.3: Production fixes for booking flow"

# 3. Push tag to GitHub
git push origin v1.2.3
```

**Version Format:** `vMAJOR.MINOR.PATCH` (e.g. `v1.2.3`)

- **MAJOR** (1.x.x) - Incompatible API changes
- **MINOR** (x.2.x) - New features (backward compatible)
- **PATCH** (x.x.3) - Bug fixes

### Step 5: Automatic Deployment

Once you push the tag, **GitHub Actions automatically**:

1. ✅ Verifies production server availability (SSH test)
2. 🐳 Builds Docker images for all services:
   - Backend (Django)
   - Telegram Bot
   - Worker (ARQ tasks)
   - Nginx
3. 📦 Tags images with three tags:
   - `latest` (most recent version)
   - `v1.2.3` (release version)
   - `sha-abc123` (git commit hash)
4. 🚢 Pushes images to GitHub Container Registry (GHCR)
5. 📋 Copies configs to VPS (`/opt/lily_website/deploy/`)
6. 🔄 Runs Django migrations (`python manage.py migrate`)
7. 📦 Collects static files (`collectstatic`)
8. 🚀 Restarts all containers on production server

### Step 6: Verify Deployment

After deployment, verify everything works:

```bash
# Check workflow status on GitHub:
# https://github.com/CodexDLC/lily_website/actions

# Or check directly on server (if SSH access available):
ssh user@<your-server-ip>

# Check containers:
docker ps

# Backend logs:
docker logs lily_website-backend --tail 50

# Bot logs:
docker logs lily_website-telegram_bot --tail 50
```

**Browser Verification:**
- Open: https://lily-salon.de/
- Open admin: https://lily-salon.de/admin/
- Verify new changes are visible on site

---

## 🛠️ Advanced Scenarios

### Scenario 1: Hotfix (urgent production fix)

If you need to fix a critical bug in production:

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-booking-error

# 2. Fix the bug
# ... edit code ...

# 3. Commit
git add .
git commit -m "fix(booking): critical error in payment validation"

# 4. Open PR directly to main
git push origin hotfix/critical-booking-error

# 5. After merging to main - create tag:
git checkout main
git pull origin main
git tag -a v1.2.4 -m "Hotfix 1.2.4: Critical booking error"
git push origin v1.2.4

# 6. Backport to develop (cherry-pick):
git checkout develop
git cherry-pick <commit-hash>  # Hash from main commit
git push origin develop
```

### Scenario 2: Rollback to Previous Version

If something breaks after release:

```bash
# 1. List tags:
git tag -l

# Output:
# v1.0.0
# v1.1.0
# v1.2.0
# v1.2.1
# v1.2.2
# v1.2.3  ← current (broken)

# 2. Rollback to previous stable tag:
git checkout main
git reset --hard v1.2.2

# 3. Create new tag for rollback:
git tag -a v1.2.4 -m "Rollback to v1.2.2 due to critical bug"
git push origin v1.2.4 --force

# GitHub Actions automatically deploys v1.2.4
```

### Scenario 3: View Changes Between Versions

To see what changed between releases:

```bash
# Compare two tags:
git log v1.2.0..v1.2.3 --oneline

# Or full diff:
git diff v1.2.0 v1.2.3

# List changed files:
git diff --name-only v1.2.0 v1.2.3
```

---

## 📝 Tag Naming Convention

### Correct Examples:

✅ `v1.0.0` - First major release
✅ `v1.2.3` - Regular release
✅ `v2.0.0` - Major update with breaking changes
✅ `v1.2.4-hotfix` - Hotfix release (optional suffix)

### Incorrect Examples:

❌ `1.2.3` - Missing `v` prefix
❌ `release-1.2.3` - Wrong format
❌ `v1.2` - Missing PATCH number

**Important:** GitHub Actions triggers only on tags starting with `v*`

---

## 🔍 Troubleshooting

### Problem 1: Deployment didn't trigger after pushing tag

**Cause:** GitHub Actions doesn't see workflow trigger.

**Solution:**
```bash
# Verify tag starts with 'v':
git tag -l

# Delete incorrect tag:
git tag -d wrong-tag
git push origin :refs/tags/wrong-tag

# Create correct tag:
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3
```

### Problem 2: GitHub Actions failed during migrations

**Cause:** Django migrations didn't apply on production.

**Solution:**
```bash
# SSH to server:
ssh user@<your-server-ip>

cd /opt/lily_website/deploy

# Check backend logs:
docker logs lily_website-backend --tail 100

# Apply migrations manually:
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate

# Restart containers:
docker compose -f docker-compose.prod.yml restart backend
```

### Problem 3: Cannot create tag (rejected)

**Cause:** Tag with this name already exists.

**Solution:**
```bash
# Delete local tag:
git tag -d v1.2.3

# Delete remote tag:
git push origin :refs/tags/v1.2.3

# Create new tag:
git tag -a v1.2.4 -m "Release 1.2.4"
git push origin v1.2.4
```

---

## 🔐 Security & Secrets

Deployment uses the following **GitHub Secrets**:

| Secret | Description |
|:---|:---|
| `HOST` | Production server IP |
| `USERNAME` | SSH user on server |
| `SSH_KEY` | Private SSH key for connection |
| `ENV_FILE` | Contents of `.env.production` file |
| `DOMAIN_NAME` | Domain name (lily-salon.de) |
| `REDIS_PASSWORD` | Redis password |

**Important:** Secrets are stored only in GitHub. Never commit `.env.production` to git!

---

## 📚 Related Documentation

- **[Russian version (for developers)](../../../ru_RU/infrastructure/deployment/releases_via_tags.md)** - Step-by-step guide in Russian
- **[Git Flow Analysis](../git_flow_analysis.md)** - Workflow strategy analysis
- **[Git Flow & Branching Strategy](../git_flow.md)** - Current branch strategy

---

## 🎯 Pre-Release Checklist

Before each release, verify:

- [ ] All features tested locally
- [ ] `check_local.ps1` ran successfully
- [ ] PR from `develop` to `main` created and CI passed
- [ ] PR merged to `main`
- [ ] Tag created in correct format (`v*.*.*`)
- [ ] Tag pushed to GitHub: `git push origin v1.2.3`
- [ ] GitHub Actions workflow started and completed successfully
- [ ] Production site verified: https://lily-salon.de/
- [ ] Backend/bot logs checked for errors
- [ ] Containers running stably (not restarting)

---

## 🔄 Migration from release Branch

If you're migrating from the old `release` branch workflow:

### Step 1: Archive release branch

```bash
# Option A: Rename to archive
git branch -m release release-archive
git push origin release-archive
git push origin --delete release

# Option B: Delete completely
git branch -D release
git push origin --delete release
```

### Step 2: Remove old workflows

Delete these files:
- `.github/workflows/cd-release.yml`
- `.github/workflows/check-release-source.yml`

The new workflow is:
- `.github/workflows/deploy-production-tag.yml` (triggers on tags)

### Step 3: Update branch protection rules

On GitHub (Settings → Branches):
1. Remove protection rules for `release` branch
2. Keep protection for `main` and `develop`

### Step 4: First tag-based release

```bash
# Merge current develop to main
git checkout main
git merge develop
git push origin main

# Create first tag
git tag -a v1.0.0 -m "Release 1.0.0: First tag-based release"
git push origin v1.0.0

# Watch deployment: https://github.com/CodexDLC/lily_website/actions
```

---

**Last Updated:** 2026-02-16
**Author:** CodexDLC
**Status:** Active (used for production releases)
