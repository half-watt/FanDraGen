# Contributing To FanDraGen

This project is set up for a small team that is still getting comfortable with Git. The goal is to keep work easy to find, easy to review, and hard to break.

## First Setup

1. Clone the repo.
2. Create and activate a virtual environment.
3. Install project dependencies:

```powershell
pip install -r requirements.txt
pip install -e .[dev]
```

4. Run the tests:

```powershell
.\run_tests.ps1
```

5. Run one demo prompt:

```powershell
.\run_demo.ps1 -Sample 0
```

## Recommended Team Workstreams

Use the repo by area, not by random file picking. The official workstream guide is in `docs/WORKSTREAMS.md`.

- `agents/`: routing, worker behavior, evaluators, delivery
- `tools/` and `data/demo/`: mocked data access, scoring logic, dataset quality
- `workflows/` and `schemas/`: orchestration, state flow, contracts
- `tests/`, `README.md`, and `docs/`: testing, documentation, polish, onboarding

If two people need the same area, split by file ownership before coding.

## Suggested Beginner-Friendly Git Workflow

1. Pull the latest `main` before starting.
2. Create a branch per task.

```powershell
git checkout main
git pull
git checkout -b feat/short-description
```

3. Make one focused change set.
4. Run tests locally.
5. Check what changed:

```powershell
git status
git diff
```

6. Commit with a clear message.

```powershell
git add .
git commit -m "Add lineup evaluator logging"
```

7. Push the branch and open a pull request.

```powershell
git push -u origin feat/short-description
```

## Branch Naming

- `feat/...` for new functionality
- `fix/...` for bug fixes
- `docs/...` for documentation-only work
- `test/...` for test-only work
- `chore/...` for repo hygiene and tooling

## Commit Message Style

Keep commit messages short and specific.

- `Add waiver pickup test coverage`
- `Update pre-playoffs demo standings`
- `Document routing and boss responsibilities`

## Pull Request Rules

- Keep each PR focused on one topic.
- Include tests when behavior changes.
- Update docs when the architecture or workflow changes.
- Ask at least one teammate to review before merging.
- Avoid large mixed PRs that touch agents, tools, tests, and docs without a clear reason.

## Where To Work

If you are unsure where a change belongs:

- behavior of an agent -> `agents/`
- how data is fetched or scored -> `tools/`
- shared model or workflow state -> `schemas/`
- orchestration and intent flow -> `workflows/`
- scenario realism -> `data/demo/`
- confidence in changes -> `tests/`
- team understanding -> `README.md` or `docs/`

## What To Avoid

- Do not work directly on `main`.
- Do not mix unrelated fixes in one branch.
- Do not change demo data without updating docs if the scenario meaning changes.
- Do not rewrite someone else’s in-progress branch without coordinating first.

## Good First Team Tasks

- improve one agent and its tests
- refine one part of the mock dataset
- add one evaluator rule and the matching tests
- improve documentation for one subsystem
- tighten the recommendation heuristics for one use case

## Project Direction

The target is a technically sound working prototype, not just a scaffold. Use `docs/FINAL_PROTOTYPE_PLAN.md` to decide whether a change moves the project toward that end state.
