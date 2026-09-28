# Code Section Template

**Purpose**: Document the implementation strategy and codebase structure. This is the bridge between architecture diagrams and actual code - what a developer needs to know to work effectively in the codebase.

## Guidance

### What This Section Should Accomplish
- Help developers navigate the codebase quickly
- Explain the "why" behind code organization choices
- Document non-obvious patterns and conventions
- Identify the most important code to understand first

### What to Include

**High-level organization**
- Don't document every folder - focus on the important structural decisions
- Explain the logic behind the folder structure
- Where does execution start? (entry points)

**Key patterns and their locations**
- Don't just name patterns - explain WHERE to find examples
- Document any custom patterns unique to this codebase
- Note deviations from standard patterns and why

**Architectural seams**
- Where are the boundaries between modules/layers?
- How do modules communicate with each other?
- What are the dependency rules? (e.g., "services can call repositories, not vice versa")

**Navigation guidance**
- Naming conventions that help find things
- Key files to read first to understand the codebase
- Dependency flow: what depends on what?

### Documenting Tricky Code

Document anything a developer would find non-obvious:
- Complex algorithms (explain the approach, not line-by-line)
- Non-obvious design decisions embedded in code
- "Magic" numbers or configuration values and what they mean
- Code that spans multiple files (explain the flow)

**Rule of thumb**: If it took you time to understand it, document it.

If an explanation would exceed 3-4 paragraphs, create a separate document and link to it.

### What NOT to Include
- ❌ Don't document obvious code
- ❌ Don't duplicate what's already in code comments
- ❌ Don't document every class - focus on architecturally significant ones
- ❌ Don't copy-paste large code blocks - reference file:line instead

### Testing Strategy

Document enough for a developer to:
- Understand the test philosophy (what gets tested, how thoroughly)
- Run tests locally
- Write new tests that follow existing patterns
- Understand test data management

---

## Template

````markdown
# Code

## Project Structure

```
src/
├── [folder]/ - [purpose and what to find here]
├── [folder]/ - [purpose and what to find here]
└── [folder]/ - [purpose and what to find here]
```

### Structure Rationale

[Brief explanation of why the code is organized this way]

## Entry Points

| Entry Point | Purpose | File |
|-------------|---------|------|
| [Main app] | [What it starts] | [path] |
| [CLI] | [What commands] | [path] |
| [Worker] | [What it processes] | [path] |

## Key Patterns

### [Pattern Name]
- **What it is**: [brief explanation]
- **Where used**: [specific locations/files]
- **Example**: [file:line reference]
- **Why we use it**: [rationale]

## Module Boundaries

[Explain how modules/layers are separated and the rules for dependencies]

| Layer/Module | Can Depend On | Cannot Depend On |
|--------------|---------------|------------------|
| [Controllers] | [Services] | [Repositories directly] |
| [Services] | [Repositories, other Services] | [Controllers] |

## Important Modules

| Module | Purpose | Start Reading Here |
|--------|---------|-------------------|
| [Name] | [What it does] | [Key file to understand first] |

## Conventions

| Area | Convention | Example |
|------|------------|---------|
| File naming | [pattern] | `user.service.ts` |
| Function naming | [pattern] | `getUserById()` |
| Error handling | [approach] | [brief description or link] |

## Code Explanations

### [Tricky Area Name]

[Concise explanation of complex code. Include code snippets only if they clarify - otherwise reference file:line]

See also: [link to detailed doc if needed]

## Testing

### Test Strategy

- **Unit tests**: [what's covered, approach]
- **Integration tests**: [what's covered, approach]
- **E2E tests**: [what's covered, approach]

### Running Tests

```bash
# [commands to run tests]
```

### Test Conventions

| Convention | Description |
|------------|-------------|
| File naming | [e.g., `*.test.ts` or `*.spec.ts`] |
| Test data | [how test data is managed] |
| Mocking | [approach to mocks/stubs] |

### Coverage

- Target: [percentage or philosophy]
- Current: [if tracked]
- Report: [how to generate/view]
````

**Auto-discover from**: Directory structure, barrel exports, common patterns in imports, test configs, README files in subdirectories
