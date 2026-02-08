# 🌿 Branching Strategy

> `docs/en_EN/infrastructure/devops/` · [README](README.md) → Branching

---

## Branch Structure

```
main (stable)
├── develop (active work)
│   ├── feature/user-auth
│   ├── feature/payments
│   └── fix/login-bug
└── release (production)
```

## Flow

### Daily Development
```
1. Create feature branch from develop:
   git checkout develop
   git checkout -b feature/my-feature

2. Work on feature, commit, push

3. Create PR: feature/my-feature → develop
   - CI Develop runs (lint)
   - Code review
   - Merge
```

### Release Cycle
```
1. Create PR: develop → main
   - CI Main runs (full tests + docker build)
   - Code review
   - Merge

2. Create PR: main → release
   - check-release-source ensures source is main
   - CD Release runs (build → deploy)
   - Merge triggers deployment
```

## Branch Rules

| Branch | Direct Push | PR Required | CI Required |
|:---|:---|:---|:---|
| `develop` | ✅ Yes | Optional | Lint on push |
| `main` | ❌ No | ✅ Yes | Tests must pass |
| `release` | ❌ No | ✅ From main only | Auto-deploy |

## GitHub Branch Protection Setup

### main branch:
- ✅ Require pull request before merging
- ✅ Require status checks to pass (ci-main / tests)
- ✅ Require branches to be up to date

### release branch:
- ✅ Require pull request before merging
- ✅ Require status checks to pass (check-source-branch)
