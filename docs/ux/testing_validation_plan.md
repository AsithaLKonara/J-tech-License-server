# Testing, Validation & Telemetry Plan

## Usability Testing

- Participants: 8–10 across personas.  
- Tasks: create animation, edit frames, apply automation, export.  
- Metrics: completion rate, time-on-task, errors, SUS score.  
- Schedule: pre-MVP and post-beta rounds.

## Heuristic Evaluation

- Use Nielsen heuristics; rate severity, feed backlog.

## A/B Testing

- Compare timeline representations, transport layouts.  
- Feature flag controlled, measure engagement/error rates.

## Automated Regression

- Visual diffs via `pytest-playwright` or similar.  
- Snapshot tests for timeline state, automation overlays, presets.

## QA Checklist

- Verify shortcuts across focus contexts.  
- Stress test with 500 frames.  
- Accessibility: contrast, focus order, screen reader labels.  
- Theme persistence across sessions.

## Telemetry & Feedback

- Instrument events: scrubbing count, playback usage, preset saves, undo.  
- Dashboard (Grafana/DataDog) for weekly review.  
- In-app feedback button leading to issue tracker or form.  
- Capture crashes with breadcrumbs.

## Experiment Workflow

1. Define hypothesis and success metric.  
2. Ship via feature flag.  
3. Collect telemetry & feedback.  
4. Decide keep/iterate/rollback.

