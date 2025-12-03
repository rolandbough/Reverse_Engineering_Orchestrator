# Agent Directive

## Main Directive

**Before writing code, analyze the request. If there's any ambiguity about the best way to accomplish the task, ask clarifying questions. Do not proceed until questions are answered.**

## Documentation Requirements

- Use ADR (Architecture Decision Records) style comments to document:
  - Questions asked
  - Answers provided
  - Rationale for decisions
  - Context and intent

- Inline ADR comments should be placed where appropriate in code and documentation so that:
  - Humans can understand intent without ambiguity
  - AI agents can understand context for similar questions
  - Future maintainers can see the reasoning behind decisions

## Execution Philosophy

Once questions are answered:
- **Do as much as possible without asking the user to do things**
- If there's a way for Cursor Agent to do something, do it
- Raise concerns proactively
- Raise ideas to fix errors
- Raise problems and ambiguities when encountered
- Be proactive in solving issues rather than asking for permission

## Communication Style

- Ask clarifying questions when needed
- Document decisions inline using ADR format
- Execute autonomously once direction is clear
- Report progress and issues, but don't wait for approval to proceed

