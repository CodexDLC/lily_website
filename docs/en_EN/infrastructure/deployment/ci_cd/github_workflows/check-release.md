# 📜 Check Release Source Workflow (`check-release-source.yml`)

[⬅️ Back](README.md) | [🏠 Docs Root](../../../../../README.md)

This GitHub Actions workflow is designed to enforce the project's Git Flow strategy, specifically for the `release` branch. It ensures that Pull Requests targeting the `release` branch originate only from the `main` branch, preventing unauthorized or out-of-flow merges.

## Trigger

*   **Event:** `pull_request`
*   **Target Branch:** `release`

## Jobs

### 1. `check-source-branch`

This job verifies the source branch of any Pull Request targeting `release`.

*   **Runs on:** `ubuntu-latest`
*   **Steps:**
    1.  **Check source branch:** This step contains a conditional check (`if: github.head_ref != 'main'`).
        *   **Logic:** If the source branch (`github.head_ref`) of the Pull Request is *not* `main`, the workflow fails.
        *   **Output:** It prints an error message to the console, explicitly stating that merges into `release` are allowed only from `main`, and then exits with a non-zero status code, causing the workflow to fail.

## Purpose

This workflow is a critical part of the Continuous Deployment (CD) pipeline's protection mechanisms. By enforcing that `release` can only be updated from `main`, it ensures:
*   **Controlled Deployment:** Only thoroughly tested and stable code (from `main`) can be deployed to production.
*   **Git Flow Adherence:** Reinforces the `develop` -> `main` -> `release` branching model.
*   **Reduced Errors:** Minimizes the risk of deploying untested features or hotfixes directly to production.
