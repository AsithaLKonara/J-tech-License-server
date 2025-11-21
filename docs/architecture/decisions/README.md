# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) documenting key design decisions for the Design Tools Tab system.

## What are ADRs?

ADRs are documents that capture important architectural decisions made during the design and development of the system. Each ADR describes:
- **Context**: The situation and problem that led to the decision
- **Decision**: The architectural choice that was made
- **Consequences**: The positive and negative outcomes of the decision

## ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](./ADR-001-layer-sync.md) | LayerManager to PatternState Sync (One-way) | ✅ Accepted |
| [ADR-002](./ADR-002-fps-duration.md) | FPS vs Frame Duration Coexistence | ✅ Accepted |
| [ADR-003](./ADR-003-signals.md) | Signal-based Communication | ✅ Accepted |
| [ADR-004](./ADR-004-instruction-sequence.md) | PatternInstructionSequence Separation | ✅ Accepted |
| [ADR-005](./ADR-005-layer-compositing.md) | Layer Compositing Strategy | ✅ Accepted |

## Format

Each ADR follows this structure:
1. **Status**: Accepted, Proposed, Deprecated, Superseded
2. **Context**: Why this decision was needed
3. **Decision**: What was decided
4. **Consequences**: Positive and negative outcomes

## When to Create an ADR

Create an ADR when:
- Making a significant architectural choice
- Choosing between multiple viable alternatives
- The decision affects multiple components
- The decision has long-term implications
- Future developers need to understand the rationale

## References

- [ADR Template](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

