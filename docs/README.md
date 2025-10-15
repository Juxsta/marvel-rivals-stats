# Marvel Rivals Stats - Documentation

## Overview

This directory contains all project documentation including product vision, specifications, and development guidelines.

## Documentation Structure

```
docs/
├── README.md                    # This file
├── PRODUCT.md                   # Product vision, goals, and roadmap
└── specs/
    ├── SPEC_TEMPLATE.md         # Template for new specifications
    ├── SPEC-001-player-discovery.md
    ├── SPEC-002-match-collection.md
    └── SPEC-003-character-analysis.md
```

## Key Documents

### [PRODUCT.md](./PRODUCT.md)
- Product vision and mission
- Target users and use cases
- Core features and roadmap
- Success criteria
- Development principles

### Specifications

Detailed technical specifications for each feature:

1. **[SPEC-001: Player Discovery](./specs/SPEC-001-player-discovery.md)**
   - Status: Approved
   - Goal: Discover 500+ players across all ranks using stratified sampling
   - Prerequisites: None
   - Next: Start implementation

2. **[SPEC-002: Match Collection](./specs/SPEC-002-match-collection.md)**
   - Status: Approved
   - Goal: Collect match histories with deduplication and rate limiting
   - Prerequisites: SPEC-001 (Player Discovery)
   - Next: Awaiting SPEC-001 completion

3. **[SPEC-003: Character Analysis](./specs/SPEC-003-character-analysis.md)**
   - Status: Approved
   - Goal: Calculate character win rates with statistical rigor
   - Prerequisites: SPEC-002 (Match Collection)
   - Next: Awaiting SPEC-002 completion

## Development Workflow

### 1. Spec-Driven Development

All features start with a specification:

```
Problem → Spec → Review → Approval → Implementation → Testing → Done
```

### 2. Creating a New Spec

1. Copy `specs/SPEC_TEMPLATE.md`
2. Name it `SPEC-XXX-feature-name.md` (next number in sequence)
3. Fill in all sections
4. Mark status as "Draft"
5. Submit for review
6. Update status to "Approved" once reviewed
7. Link implementation tasks

### 3. Implementing a Spec

1. Read spec thoroughly
2. Check dependencies are completed
3. Create implementation tasks from spec's task list
4. Write tests per spec's testing plan
5. Implement feature
6. Verify success criteria met
7. Update spec status to "Implemented"

### 4. Spec Status Workflow

- **Draft**: Being written, not ready for review
- **In Review**: Ready for feedback and discussion
- **Approved**: Ready for implementation
- **Implemented**: Feature complete and merged
- **Deprecated**: No longer relevant (keep for historical reference)

## Specification Guidelines

### Required Sections

Every spec must have:
- **Problem Statement**: What are we solving?
- **Goals**: What do we want to achieve?
- **Non-Goals**: What are we NOT doing?
- **User Stories**: Who benefits and how?
- **Proposed Solution**: Technical design and approach
- **Success Criteria**: How do we know it works?
- **Implementation Tasks**: Checklist of work items

### Best Practices

1. **Be Specific**: Vague specs lead to unclear implementations
2. **Consider Alternatives**: Document why you chose this approach
3. **Think About Risks**: What could go wrong?
4. **Define Success**: Clear, testable criteria
5. **Break Down Tasks**: Small, implementable units of work
6. **Link Dependencies**: Reference related specs

## Current Development Phase

**Phase**: MVP (Minimum Viable Product)

**Goal**: Prove the concept with basic character win rate analysis

**Status**:
- [x] Project scaffolding
- [x] Database schema
- [x] API client
- [x] Documentation structure
- [x] Initial specs written
- [ ] SPEC-001 implementation (Next)
- [ ] SPEC-002 implementation
- [ ] SPEC-003 implementation

## Contributing to Docs

### Adding a New Spec

1. Follow the template structure
2. Number sequentially (SPEC-004, SPEC-005, etc.)
3. Link prerequisites and dependencies
4. Get review before marking "Approved"

### Updating Existing Docs

1. Update the "Updated" date
2. Document changes in spec if substantial
3. Keep old versions for reference if needed

### Documentation Standards

- Use Markdown for all docs
- Include code examples where helpful
- Link between related documents
- Keep implementation details in specs, not README
- Use clear, concise language

## Questions?

Refer to:
- `PRODUCT.md` for high-level vision
- Individual specs for feature details
- `../PLAN.md` for overall implementation plan
- `../README.md` for quick start guide
