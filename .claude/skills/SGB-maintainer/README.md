# SGB-maintainer Skill

A Claude/Roo Code skill for creating and maintaining **Software Guidebooks** following Simon Brown's methodology from *"Software Architecture for Developers Vol. 2"*.

## Overview

The SGB-maintainer skill automates the creation of comprehensive architecture documentation by analyzing your codebase and generating a structured Software Guidebook using the C4 model. It's designed to help teams:

- **Onboard new developers** with clear, navigable documentation
- **Document architecture decisions** systematically
- **Create C4 diagrams** (Context, Container, Component) in Mermaid syntax
- **Maintain living documentation** that evolves with the codebase

## When to Use

Activate this skill when you need to:

| Trigger Phrase | Use Case |
|----------------|----------|
| `create guidebook` | Generate a new Software Guidebook from scratch |
| `update guidebook` | Update existing documentation after code changes |
| `document architecture` | Create architecture documentation |
| `create C4 diagrams` | Generate C4 model diagrams |
| `help new developer understand codebase` | Create onboarding documentation |
| `/sgb` | Quick shortcut to invoke the skill |

## Output Structure

The skill generates documentation in `docs/software-guidebook/` with 14 chapters:

```
docs/software-guidebook/
├── 00-index.md              # Table of contents + commit reference
├── 01-context.md            # System scope, users, external systems
├── 02-functional-overview.md # Key features and use cases
├── 03-quality-attributes.md  # Non-functional requirements
├── 04-constraints.md         # Constraints the team cannot change
├── 05-principles.md          # Architecture and design principles
├── 06-software-architecture.md # C4 diagrams (Container, Component)
├── 07-external-interfaces.md  # APIs, integrations, protocols
├── 08-code.md                # Code organization, patterns, conventions
├── 09-data.md                # Data models, storage, migrations
├── 10-infrastructure.md      # Deployment environments, networking
├── 11-deployment.md          # Build, release, deployment process
├── 12-operation-support.md   # Monitoring, troubleshooting, runbooks
└── 13-decision-log.md        # Architecture Decision Records
```

## Setup: OPENROUTER_KEY Environment Variable

This skill requires an LLM provider to function. If you're using [OpenRouter](https://openrouter.ai/) as your API provider, you'll need to set the `OPENROUTER_KEY` environment variable.

### Getting Your OpenRouter API Key

1. Create an account at [openrouter.ai](https://openrouter.ai/)
2. Navigate to **Keys** in your dashboard
3. Click **Create Key** and copy the generated key

### Setting the Environment Variable

#### macOS / Linux (Bash/Zsh)

**Temporary (current session only):**
```bash
export OPENROUTER_KEY="sk-or-v1-your-api-key-here"
```

**Permanent (add to shell profile):**

For **Bash** users, add to `~/.bashrc` or `~/.bash_profile`:
```bash
echo 'export OPENROUTER_KEY="sk-or-v1-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

For **Zsh** users (default on modern macOS), add to `~/.zshrc`:
```bash
echo 'export OPENROUTER_KEY="sk-or-v1-your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**Verify it's set:**
```bash
echo $OPENROUTER_KEY
```

#### Windows

**Command Prompt (temporary, current session only):**
```cmd
set OPENROUTER_KEY=sk-or-v1-your-api-key-here
```

**PowerShell (temporary, current session only):**
```powershell
$env:OPENROUTER_KEY = "sk-or-v1-your-api-key-here"
```

**Permanent (System Environment Variables):**

1. Press `Win + R`, type `sysdm.cpl`, and press Enter
2. Go to the **Advanced** tab
3. Click **Environment Variables**
4. Under **User variables**, click **New**
5. Set:
   - **Variable name:** `OPENROUTER_KEY`
   - **Variable value:** `sk-or-v1-your-api-key-here`
6. Click **OK** to save
7. Restart your terminal or IDE

**PowerShell (permanent for current user):**
```powershell
[Environment]::SetEnvironmentVariable("OPENROUTER_KEY", "sk-or-v1-your-api-key-here", "User")
```

**Verify it's set:**
```powershell
$env:OPENROUTER_KEY
# or in Command Prompt:
echo %OPENROUTER_KEY%
```

## Background

### The Software Guidebook Concept

The Software Guidebook is a documentation approach created by **Simon Brown**, author of the C4 model for visualizing software architecture. Unlike traditional documentation that often becomes outdated, a Software Guidebook is designed to be:

- **Concise** — Readable in a few hours, not days
- **Audience-focused** — Written for new team members joining tomorrow
- **Living** — Integrated with version control relative to specific commits
- **Decision-oriented** — Explains *why*, not just *what*

### The C4 Model

The skill generates diagrams following the C4 model hierarchy:

1. **Context Diagram** — Shows your system in the context of users and external systems
2. **Container Diagram** — High-level technical building blocks (apps, databases, queues)
3. **Component Diagram** — Components within a container (modules, services)
4. **Code Diagram** — (Optional) Class/module level details

All diagrams are generated in **Mermaid syntax** for easy rendering in Markdown.

### Role of This Skill

The [`SKILL.md`](SKILL.md) file contains the prompt instructions that guide the AI assistant. It defines:

- **Triggers** — What phrases activate the skill
- **Workflow** — Step-by-step process for creating/updating documentation
- **Output structure** — Which files to generate and their purposes
- **Section guidelines** — What each chapter should contain
- **Verification process** — How to validate the generated documentation
- **C4 diagram rules** — How to create accurate architecture diagrams

### Reference Materials

This skill includes reference materials in the [`references/`](references/) directory:

- [`c4-mermaid.md`](references/c4-mermaid.md) — C4 Mermaid syntax guide
- [`sections/`](references/sections/) — Templates for each guidebook chapter

Additionally, the skill draws from Simon Brown's works (included as PDFs):
- *Software Architecture for Developers Vol. 2*
- *The C4 model for visualising software architecture*

## Usage Examples

### Creating a New Guidebook

```
User: /sgb
Assistant: I'll create a Software Guidebook for this codebase...
```

Or be more explicit:

```
User: Create a software guidebook for this project
```

### Updating an Existing Guidebook

```
User: Update the software guidebook to reflect recent changes
```

The skill will:
1. Read the existing guidebook
2. Compare against the current codebase state via git diff
3. Identify and propose updates to outdated sections

### Documenting Specific Aspects

```
User: Update the C4 diagrams in the software guidebook
User: Add new ADRs to the decision log
User: Document the new payment integration in the external interfaces chapter
```

## Verification

After generating documentation, the skill spawns **isolated verification subagents** that:

1. Check **factual accuracy** — File paths, port numbers, API endpoints, versions
2. Evaluate **audience value** — Is it useful for new team members?
3. Identify **omissions** — Missing topics, incomplete sections, undefined terms

No fixes are applied automatically — all proposed changes require user approval.

## Related Skills

- **documentation** — Writing style guidelines used for prose
- **documentation-referencing** — Guidelines for adding source references
- **diagram-improver** — Enhances Mermaid diagram visual appearance

## License

This skill references Simon Brown's C4 model and Software Guidebook methodology. Please refer to the included PDF materials for attribution.
