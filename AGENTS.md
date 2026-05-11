<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- **Mandatory Agent Skills**: `proposal-checker`, `validate-proposal`, and `apply-spec-proposal-iteratively`.
- **Sequential Implementation Protocol**: Tasks MUST be completed one by one and verified.
- **Task List Format Guardrails**: Strict sequential format for `tasks.md`.
- How to create and apply change proposals.
- Spec format and conventions.

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->