# 🔄 Migration Guide: From Release Branch to Tags

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

---

## 📋 Overview

This guide explains how to migrate from the old `release` branch workflow to the new tag-based deployment workflow.

**Goal:** Remove the `release` branch and associated workflows, enable tag-based deployments.

---

## ✅ Pre-Migration Checklist

Before starting migration:

- [ ] No active deployments in progress
- [ ] All pending PRs to `release` branch merged or closed
- [ ] Team notified about workflow change
- [ ] Latest code from `release` synced to `main` and `develop`

---

## 🚀 Migration Steps

### Step 1: Verify New Workflow Exists

**File created:** `.github/workflows/deploy-production-tag.yml`

This workflow triggers on tags matching `v*` pattern (e.g., `v1.2.3`).

**Verify:**
```bash
ls -la .github/workflows/deploy-production-tag.yml
```

### Step 2: Archive or Delete Release Branch

**Option A: Archive (Recommended for history preservation)**

```bash
# Rename release to release-archive
git branch -m release release-archive

# Push archived branch
git push origin release-archive

# Delete old release branch from remote
git push origin --delete release
```

**Option B: Delete Completely**

```bash
# Delete local branch
git branch -D release

# Delete remote branch
git push origin --delete release
```

### Step 3: Remove Old Workflows

**Delete these files:**
1. `.github/workflows/cd-release.yml` - Old release branch deployment
2. `.github/workflows/check-release-source.yml` - Release branch protection

```bash
git checkout develop
git rm .github/workflows/cd-release.yml
git rm .github/workflows/check-release-source.yml
git commit -m "chore(ci): remove release branch workflows, migrate to tag-based deployment"
git push origin develop
```

### Step 4: Update GitHub Branch Protection Rules

**On GitHub: Settings → Branches**

#### Remove Protection for `release` Branch:

1. Go to repository Settings
2. Click "Branches" in left sidebar
3. Find "Branch protection rules"
4. Delete rule for `release` branch (if exists)

#### Verify Protection for Main Branches:

**For `main` branch:**
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
  - ✅ CI Tests (pytest, mypy, ruff)
  - ✅ Docker build check
- ✅ Require branches to be up to date before merging
- ❌ Do not require deployments to succeed (we deploy via tags now)

**For `develop` branch:**
- ✅ Require pull request reviews (optional for solo developer)
- ✅ Require status checks to pass before merging
  - ✅ Linters (ruff, mypy)

### Step 5: Test Tag-Based Deployment

**Create a test tag:**

```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Create test tag
git tag -a v1.0.0-test -m "Test tag-based deployment"

# Push tag
git push origin v1.0.0-test
```

**Verify workflow execution:**

1. Go to: `https://github.com/CodexDLC/lily_website/actions`
2. Find workflow run: "Deploy Production (Tag-based)"
3. Verify all jobs pass:
   - ✅ Check Server Availability
   - ✅ Build & Deploy to VPS

**If successful, delete test tag:**

```bash
git tag -d v1.0.0-test
git push origin :refs/tags/v1.0.0-test
```

### Step 6: First Production Release

**Create first official tag:**

```bash
git checkout main
git pull origin main

# Use semantic versioning
git tag -a v1.0.0 -m "Release 1.0.0: First tag-based production release"

git push origin v1.0.0
```

**Monitor deployment:**
- Watch GitHub Actions: `https://github.com/CodexDLC/lily_website/actions`
- Verify production: `https://lily-salon.de/`
- Check logs on VPS (if SSH access available)

---

## 🔍 Verification Steps

After migration, verify:

### 1. Workflows

```bash
# List workflows
ls -la .github/workflows/

# Should have:
# ✅ deploy-production-tag.yml  (new tag-based deployment)
# ✅ ci-develop.yml             (develop branch CI)
# ✅ ci-main.yml                (main branch CI)

# Should NOT have:
# ❌ cd-release.yml             (removed)
# ❌ check-release-source.yml   (removed)
```

### 2. Branches

```bash
# List branches
git branch -a

# Should have:
# ✅ develop
# ✅ main
# ✅ release-archive (if you archived)

# Should NOT have:
# ❌ release (deleted)
```

### 3. Tags

```bash
# List tags
git tag -l

# Should see:
# v1.0.0
# v1.0.0-test (if you kept it)
```

### 4. GitHub Settings

**Branch Protection Rules:**
- ✅ `main` - protected, requires PR + CI
- ✅ `develop` - protected, requires linters
- ❌ `release` - rule deleted

---

## 📝 Update Documentation References

**Update these files to reflect new workflow:**

1. **Main README.md** - Update deployment instructions
2. **docs/en_EN/infrastructure/git_flow.md** - Remove `release` branch section
3. **Contributing guides** - Update release process
4. **Team onboarding docs** - Update workflow instructions

**Files already updated:**
- ✅ `docs/en_EN/infrastructure/deployment/releases_via_tags.md` - Full guide
- ✅ `docs/ru_RU/infrastructure/deployment/releases_via_tags.md` - Russian guide
- ✅ `docs/en_EN/infrastructure/git_flow_analysis.md` - Analysis document

---

## 🛠️ Rollback Plan (If Migration Fails)

If something goes wrong, you can quickly rollback:

### Restore release Branch

```bash
# If archived:
git checkout release-archive
git branch -m release-archive release
git push origin release

# If deleted, restore from commit:
git checkout <last-commit-hash-of-release>
git checkout -b release
git push origin release
```

### Restore Old Workflows

```bash
git checkout <commit-before-deletion>
git restore .github/workflows/cd-release.yml
git restore .github/workflows/check-release-source.yml
git add .github/workflows/
git commit -m "chore(ci): restore release branch workflows"
git push origin develop
```

### Re-enable Branch Protection

Go to GitHub Settings → Branches → Add rule for `release`

---

## ❓ Troubleshooting

### Problem: Tag deployment doesn't trigger

**Cause:** Workflow file not in `main` branch

**Solution:**
```bash
# Ensure workflow is in main
git checkout main
git merge develop
git push origin main
```

### Problem: Old workflows still running

**Cause:** Workflows not deleted from main branch

**Solution:**
```bash
git checkout main
git rm .github/workflows/cd-release.yml
git rm .github/workflows/check-release-source.yml
git commit -m "chore(ci): remove old workflows from main"
git push origin main
```

### Problem: Cannot delete release branch (protected)

**Cause:** Branch protection rules prevent deletion

**Solution:**
1. Go to GitHub Settings → Branches
2. Remove protection rule for `release`
3. Then delete: `git push origin --delete release`

---

## 📚 Related Documentation

- **[Tag-Based Releases Guide](./releases_via_tags.md)** - How to use new workflow
- **[Git Flow Analysis](../git_flow_analysis.md)** - Why we migrated
- **[CI/CD Documentation](./ci_cd/README.md)** - GitHub Actions overview

---

## 🎯 Migration Checklist

Complete migration checklist:

- [ ] **Step 1:** Verified `deploy-production-tag.yml` exists
- [ ] **Step 2:** Archived or deleted `release` branch
- [ ] **Step 3:** Removed old workflows (`cd-release.yml`, `check-release-source.yml`)
- [ ] **Step 4:** Updated GitHub branch protection rules
- [ ] **Step 5:** Tested tag-based deployment with test tag
- [ ] **Step 6:** Created first production release tag
- [ ] **Verification:** All checks passed
- [ ] **Documentation:** Updated all relevant docs
- [ ] **Team:** Notified team of workflow change

---

**Migration Date:** 2026-02-16
**Status:** Migration Guide (use once to migrate from release branch)
**Next Steps:** Follow [releases_via_tags.md](./releases_via_tags.md) for regular releases
