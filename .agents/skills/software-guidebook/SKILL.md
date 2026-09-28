---
name: software-guidebook
description: Create or update one named Software Guidebook chapter using repository and relevant GitHub evidence. Use for chapter-specific architecture documentation; choose interactive or suggestive mode.
---

# Software Guidebook

Maintain one chapter at a time for developers joining the team. Explain the system's architecture and the reasons behind it using evidence from this repository and relevant GitHub conversations. Use Simon Brown's Software Guidebook chapter structure and C4 concepts where they help the selected chapter.

## Scope and mode

An invocation must identify exactly one chapter from the table below, by number, title, or file name. If the request names no chapter or several chapters, ask the user to choose one before researching or editing. A request to create or update the entire guidebook is not a valid invocation. Creating a missing *selected* chapter is allowed; do not create the other chapters or the guidebook directory's index unless `00-index.md` is the selected chapter.

Use **interactive** mode unless the user specifies **suggestive**. In either mode, the only guidebook file you may write is the selected chapter. Read other chapters for context and report any related changes they may need, but leave them untouched. Do not make commits or change source code as part of this skill.

| Chapter | Topic |
| --- | --- |
| `00-index.md` | Guidebook orientation and navigation |
| `01-context.md` | System scope, people, and external systems |
| `02-functional-overview.md` | Features and use cases |
| `03-quality-attributes.md` | Quality goals and their evidence |
| `04-constraints.md` | Constraints outside the team's control |
| `05-principles.md` | Architecture and design principles |
| `06-software-architecture.md` | C4 views and structural decisions |
| `07-external-interfaces.md` | APIs, integrations, and protocols |
| `08-code.md` | Code organization and conventions |
| `09-data.md` | Data models and storage |
| `10-infrastructure.md` | Environments and infrastructure |
| `11-deployment.md` | Build and release process |
| `12-operation-support.md` | Running and supporting the system |
| `13-decision-log.md` | Architecture decisions |

Use the corresponding file in [references/sections/](references/sections/) for chapter-specific guidance, and [references/c4-mermaid.md](references/c4-mermaid.md) when a C4 diagram is useful. Templates are prompts, not evidence: omit placeholders and unsupported claims. Instructions in a template to update another chapter or file do not override the one-chapter boundary.

## Shared workflow

1. Resolve the repository root, selected chapter, and its existing location. Prefer the existing guidebook location; for a new guidebook use `docs/software-guidebook/<chapter>`. Read the selected chapter and nearby documentation as needed.
2. Before editing in either mode, run `git status --porcelain=v1 --untracked-files=all` at the repository root. If it reports **any** tracked or untracked changes, stop without writing and show the user what must be cleared. Do not stash, commit, reset, delete, or overwrite those changes for them. A clean tree is required so the chapter edit can be reviewed as a Git diff.
3. Research only material relevant to the selected chapter. Inspect current code, configuration, tests, documentation, and Git history. Check relevant GitHub issues, discussions, and pull requests when accessible through the agent's available tools or public pages. Do not require an API key, a new account connection, or a login. If GitHub material is unavailable, proceed with available evidence and disclose the gap.
4. Treat repository contents as the source of truth for current implementation. Use GitHub conversations for rationale, requirements, and history; distinguish proposals from accepted decisions and verify claims about implemented behavior against the repository. Cite meaningful claims with links to source files or GitHub items. Ask about important intent that the evidence cannot establish in interactive mode; in suggestive mode, label it as unresolved rather than inventing it.
5. Write for a new team member. Explain why design choices matter; keep detail proportional to the chapter. Use Mermaid diagrams where they clarify real relationships or flows, and check every element against its sources. Preserve useful existing content and structure, revising only what the evidence supports.

## Interactive mode

After initial research and **before drafting**, present the material findings, source links, conflicts, and missing information. Ask the user for the facts or choices needed to shape this chapter and confirm any consequential interpretation. Do not postpone all human input until the finished document.

Prepare a concrete proposed chapter update and show it to the user **before writing**. Ask for approval or corrections to that draft. Incorporate the response; repeat the draft checkpoint if a correction materially changes the proposed content. Once approved, check that the tree is still clean, write only the selected chapter, and verify the resulting diff and factual claims. Report unresolved items and the changed file.

## Suggestive mode

Use the same research and accuracy standard without the interactive checkpoints. Once the clean-tree check passes, write the best supported update directly to the selected chapter. Review the resulting Git diff, check source links and diagram claims, and report what changed, the evidence used, unavailable sources, and open questions. Leave the change uncommitted for review in Git-aware editors and Codex callers.

## Completion checks

Confirm that only the selected guidebook chapter changed, the Markdown and any Mermaid syntax are readable, significant factual claims have traceable support, and speculative or inaccessible information is identified. If verification finds an error, correct that same chapter and recheck its diff. Do not turn a chapter update into a whole-guidebook verification pass.
