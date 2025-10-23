# Plan Design Guidelines

## Core Principle
RULE #0: DO NOT OVERENGINEER. Start with the simplest solution that works; add complexity only with evidence.

Prefer boring technology: use proven, familiar tools unless you have a compelling reason otherwise.

## Design Rules
1) Solve Today's Problem
- Build for current requirements (YAGNI).
- Prefer straightforward code (KISS).
- Question every abstraction: does it solve a current pain?

2) Test-Driven Development (TDD)
- Red → Green → Refactor.
- Write minimal code to pass; refactor under green.

3) Incremental, End-to-End
- Start with a walking skeleton.
- Add one capability at a time.
- Ship early and gather feedback.

4) Optimize Last
- Make it work → right → fast.
- Profile before optimizing.

5) Structured Plan Format
- Hierarchical numbered steps with checkboxes (1, 1.1, 1.2.1).
- Each step includes an outcome and acceptance criteria.

Example:
- [ ] 1. Setup project
  - [ ] 1.1. Initialize repository
- [ ] 2. Implement feature
  - [ ] 2.1. Write tests

## Execution Guardrails
- Definition of Done: tests passing, code quality checks, docs/monitoring updated, automated deployment.
- Acceptance Criteria: Given/When/Then or observable outcomes.
- Change Control: log scope changes, estimate impact, re-prioritize.
- Risk Log: top risks with mitigations and owners; review regularly.
- Blockers & Dependencies: flag blockers and dependencies; escalate quickly.
- Rollback Strategy: every change should be revertible; maintain rollback capability.

## Non-Functional Requirements
- Define targets: performance (p50/p95), reliability (SLO/SLA), security, privacy, accessibility, observability, cost.

## Feedback and Review
- Demos/reviews every 1–2 increments.
- Validate with telemetry or user tests.
- Define measurable success criteria before starting.
- Define stakeholder sync points upfront.

## Complexity Checklist

**Add complexity when:**
- ≥3 call sites or painful duplication.
- Profiled bottleneck.
- Safety/security/compliance need.
- Net complexity decreases now.

**Avoid (red flags):**
- "Just in case" abstractions.
- Designing for scale you don't have.
- Over-configuring constants.
- Single-implementation interfaces.
- Pattern use without a problem.

## When in Doubt
Ask: "What's the simplest thing that could possibly work?" Then do only that.
