# Final Prototype Plan

This document defines what the team should aim for by the end of the project.

The goal is not just to have code that runs. The goal is to have a working prototype that is technically sound, understandable, demonstrable, and believable.

## Final Product Standard

By the end of the project, FanDraGen should be able to do all of the following in a stable demo:

1. accept a supported NBA fantasy prompt
2. route it correctly
3. show boss-agent orchestration and tool usage
4. use data that feels close to actual NBA late-season conditions
5. produce grounded recommendations or explanations
6. run evaluators and show revision behavior when needed
7. mark approval-required actions instead of pretending to execute them
8. return both structured JSON and readable markdown
9. show logs, metrics, and traceability
10. pass a deterministic test suite

## What “Technically Sound” Means For This Project

- state flow is explicit and inspectable
- modules have clear ownership boundaries
- mock data supports the actual demo claims
- tools return structured evidence, not just strings
- recommendations are justified and testable
- the demo does not depend on hidden manual steps
- the repo is understandable to a new teammate within one session

## Required Improvements From The Current Baseline

### Data Realism

- make standings, schedules, injuries, seeding pressure, and waiver context feel closer to real NBA late-season dynamics
- expand roster context and matchup context
- strengthen the realism of player news and lineup volatility

### Orchestration Quality

- make routing more robust than simple keywords where practical
- reduce duplicated workflow logic
- improve boss-agent task planning and revision visibility

### Recommendation Quality

- improve scoring logic beyond the first-pass heuristic where possible
- better reflect roster needs, risk, and late-season rest patterns
- make draft, trade, waiver, and lineup outputs more nuanced

### Evaluation Quality

- ensure poor answers really fail evaluation
- ensure revised answers actually improve on the first attempt
- make grounding coverage visible and meaningful

### Demo Quality

- make the sample outputs presentation-ready
- choose the strongest prompts for a live walkthrough
- prepare one fallback example and one approval-gating example on purpose

## Suggested Milestone Sequence

### Milestone 1: Repo Stability

- all contributors can run the repo locally
- branch workflow is understood
- tests pass for everyone

### Milestone 2: Strong Core Demo

- onboarding, draft, lineup, trade, waiver, news, explanation, and fallback prompts all behave credibly
- logs and traces clearly show the architecture

### Milestone 3: Realism Upgrade

- data becomes more NBA-like
- recommendation logic reflects late-season reality better
- documentation explains those improvements clearly

### Milestone 4: Final Presentation Build

- demo scripts are stable
- sample outputs are curated
- README, architecture notes, and contribution docs are polished
- the team can explain both how it works and why it is designed this way

## Final Deliverables The Team Should Expect

- a working repo that can be run locally from a clean setup
- deterministic tests that pass
- a realistic mocked NBA scenario
- a clear architecture explanation
- a strong demo flow for presentation
- documented future steps for real APIs, stronger retrieval, and model-based scoring

## Final Presentation Checklist

- explain the architecture in one minute
- show one recommendation prompt end to end
- show one fallback prompt end to end
- point out tool calls, evaluator behavior, and approval gating in the trace
- show that the repo is organized enough for a team project, not just a single-person script bundle
