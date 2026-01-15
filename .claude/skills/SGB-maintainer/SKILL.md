---
name: SGB-maintainer
description: Create and maintain Software Guidebooks following Simon Brown's methodology from "Software Architecture for Developers Vol. 2". Use this skill when the user asks to "create guidebook", "update guidebook", "document architecture", "create C4 diagrams", "create architecture docs", "help new developer understand codebase", or "create onboarding docs". Generates comprehensive documentation with auto-analysis of the codebase.
---

# Software Guidebook Maintainer

You are an expert technical writer and software architect.
Your task is to generate a comprehensive and accurate software guidebook in Markdown format.
This skill creates and maintains Software Guidebooks following Simon Brown's C4 model methodology. It auto-analyzes codebases to generate comprehensive architecture documentation.

## Triggers

Activate on:
- "create guidebook", "update guidebook", "software guidebook"
- "document architecture", "architecture documentation"
- "create C4 diagrams", "C4 model"
- "help new developer understand codebase", "onboarding docs"
- "/sgb"

## Output Structure

Create `docs/software-guidebook/` with the following sections. Load section templates from `references/sections/` as needed.

| Output File | Purpose | Template | Auto-discover From |
|-------------|---------|----------|-------------------|
| 00-index.md | Table of contents and navigation | `00-index.md`, also contains the id of the commit that this documentation will represent | - |
| 01-context.md | System scope, users, external systems | `01-context.md` | README, docs/, OAuth configs, API client configs, env files |
| 02-functional-overview.md | Key features and use cases | `02-functional-overview.md` | Route handlers, CLI commands, main entry points |
| 03-quality-attributes.md | Non-functional requirements | `03-quality-attributes.md` | Test configs, CI thresholds, security configs, SLA docs |
| 04-constraints.md | Constraints the team cannot change | `04-constraints.md` | Corporate policies, regulatory requirements, organizational mandates |
| 05-principles.md | Architecture and design principles | `05-principles.md` | ARCHITECTURE.md, CONTRIBUTING.md, .eslintrc, ADRs |
| 06-software-architecture.md | C4 diagrams (Container, Component) | `06-software-architecture.md` | src/ structure, package boundaries, module imports |
| 07-external-interfaces.md | APIs, integrations, protocols | `07-external-interfaces.md` | OpenAPI specs, GraphQL schemas, webhook handlers |
| 08-code.md | Code organization, patterns, conventions | `08-code.md` | Directory structure, barrel exports, import patterns |
| 09-data.md | Data models, storage, migrations | `09-data.md` | Schema files, ORM models, migrations, database configs |
| 10-infrastructure.md | Deployment environments, networking | `10-infrastructure.md` | docker-compose, k8s manifests, terraform, cloud configs |
| 11-deployment.md | Build, release, deployment process | `11-deployment.md` | CI/CD pipelines, Makefile, scripts/, deploy configs |
| 12-operation-support.md | Monitoring, troubleshooting, runbooks | `12-operation-support.md` | Monitoring configs, logging setup, incident docs |
| 13-decision-log.md | Architecture Decision Records | `13-decision-log.md` | docs/adr/, docs/decisions/, existing ADRs |

## Style
Use the 'documentation' skill for writing style.

## Workflow

### Creating a New Guidebook
1. **Create a commit** check if the working directory has uncomitted changes. If so, propose to the user to commit and present a commit message. Then give the user the option of using that message, editing that message, supplying their own message or doing the entire commit themselves. Take note of the id of the new commit (or the latest one if the working directory was clean) because it must be included in the 00-index.md file.
2. **Analyze the codebase** using Glob, Grep, and Read tools:
   - Identify tech stack, frameworks, languages
   - Find configuration files (package.json, docker-compose, etc.)
   - **Verify config files exist** before documenting them (check for `.sample` or `.example` variants)
   - Discover API routes, database schemas, entry points
   - Locate existing documentation

3. **Create the directory structure** at `docs/software-guidebook/`

4. **Generate each section** by:
   - Reading relevant source files
   - Inferring architecture from code structure
   - Considering what information (that isn't easily available in the codebase itself) is helpful for new team members
   - Creating C4 diagrams where relevant, and UML diagrams where helpful, both in Mermaid syntax
   - **Always use Mermaid** for sequence diagrams (not ASCII art)
   - Documenting patterns and conventions found

5. **Populate chapters in this sequence** (concrete → abstract):
   1. `09-data.md` - Data models, storage
   2. `08-code.md` - Code organization, patterns
   3. `10-infrastructure.md` - Deployment environments
   4. `11-deployment.md` - Build, release process
   5. `13-decision-log.md` - Architecture decisions
   6. `06-software-architecture.md` - C4 diagrams
   7. `07-external-interfaces.md` - APIs, integrations
   8. `02-functional-overview.md` - Features, use cases
   9. `01-context.md` - System scope, users
   10. `04-constraints.md` - External constraints
   11. `03-quality-attributes.md` - Non-functional requirements
   12. `05-principles.md` - Design principles
   13. `12-operation-support.md` - Monitoring, runbooks
   14. `00-index.md` - Table of contents (last). Also include a the commit id of (and a github link to) the exact commit for which these docs were created or updated.

   This sequence starts with what can be auto-discovered from code, then builds up to sections requiring user input.

### Updating an Existing Guidebook

1. Propose to commit if there are uncomitted changes.
2. Read existing guidebook sections
3. Read a git diff between the commit that is mentioned in the 00-index.md and the latest commit. 
4. Compare against current codebase state
5. Identify outdated sections
6. Propose updates with clear diffs

### Post-Creation and Post-update steps.

After creating or updating Software Guidebook chapters, the Software Guidebook content must be verified, and the diagrams must be improved.

#### Verification

After all chapters have been created or updated, the entire Software Guidebook **must** undergo a thorough verification process. This verification is critical for ensuring documentation quality and must be executed by one or more **subagents with isolated context** to ensure that errors made during creation do not bias the verification.

##### Why Isolated Subagent Verification?

When the same context is used for both creation and verification:
- Confirmation bias can cause overlooking of errors
- Assumptions made during writing persist into review
- "Fresh eyes" catch issues that the original author misses

By spawning subagent tasks, each verifier starts with a clean context and evaluates the documentation independently against the actual codebase.

##### Verification Checks (in priority order)

**1. Factual Accuracy (CRITICAL - highest priority)**

A subagent must verify every factual claim against the codebase:
- **File paths and names**: Do referenced files actually exist?
- **Port numbers and URLs**: Match what's in code/config?
- **API endpoints**: Correct paths, methods (GET/POST), parameters?
- **Technology versions**: Match package.json, Dockerfile, requirements.txt?
- **Environment variables**: Listed vars exist and are correctly described?
- **Code snippets**: Accurate and from the correct source files?
- **Diagram accuracy**: C4 diagrams reflect actual architecture?
- **Configuration files**: Referenced configs exist (not `.sample` or `.example` only)?

For each factual issue found, report:
```markdown
| Location | Claim | Actual | Severity |
|----------|-------|--------|----------|
| [chapter:section] | [what doc says] | [what code shows] | Critical/Major/Minor |
```

**2. Value and Relevance for Target Audience**

A subagent must evaluate whether each section serves new team members effectively:
- **Audience fit**: Is the content appropriate for developers joining the team?
- **Actionable information**: Can readers use this to work effectively?
- **Right level of detail**: Not too shallow, not too deep?
- **Missing context**: Does the reader need more background?
- **Unnecessary content**: Is there information that adds no value?
- **Clarity**: Would an intelligent reader unfamiliar with this codebase understand?

For each relevance issue found, report:
```markdown
| Location | Issue | Suggested Improvement | Priority |
|----------|-------|----------------------|----------|
| [chapter:section] | [problem description] | [proposed fix] | High/Medium/Low |
```

**3. Omissions and Ambiguities**

A subagent must identify gaps and unclear areas:
- **Missing topics**: Important aspects of the system not covered?
- **Incomplete sections**: Topics mentioned but not fully explained?
- **Ambiguous statements**: Phrases that could be interpreted multiple ways?
- **Undefined terms**: Domain or technical terms used without explanation?
- **Missing cross-references**: Related topics not linked?
- **Outdated TODO markers**: Placeholders that should have been filled?

For each omission/ambiguity found, report:
```markdown
| Location | Type | Description | Suggested Action |
|----------|------|-------------|------------------|
| [chapter:section] | Omission/Ambiguity | [what's missing or unclear] | [how to fix] |
```

##### Verification Process

1. **Spawn verification subagent(s)** 
   - in Roo Code: Use the `new_task` tool with `ask` mode to spawn a subagent.
   - in Claude Code: Use the `Task` tool with the `Explore` agent type.
   - Pass the guidebook file paths
   - Subagent receives fresh context with no memory of creation process
   - Each subagent focuses on all verification categories

2. **Subagent execution**:
   * Read the generated guidebook chapters
   * Cross-reference claims against actual codebase using tools for
     - reading files, 
     - performing searches, 
     - using Language Server Protocol, if available,
     - consulting a codebase index (RAG) if available.
   * Build a structured report of findings

3. **Report findings to user**:
   - Present all issues organized by priority (factual accuracy first)
   - Include concrete, actionable fix proposals for each issue
   - Use tables for easy scanning
   - Highlight critical issues that could mislead readers

4. **Await user decision**:
   - **No fixes are applied autonomously**
   - User reviews findings and approves, modifies, or rejects each proposal
   - Only after explicit user approval are changes made

##### Subagent Task Template

When spawning a verification subagent, use this template:

```xml
You are a fresh reviewer verifying a Software Guidebook for accuracy and quality.
You have NO prior context about how this documentation was created.

<task>
Verify the following guidebook chapters against the actual codebase:
- [list of chapter files to verify]
</task>

<checklist>
1. Factual Accuracy (CRITICAL)
- [ ] All file paths exist
- [ ] Port numbers match code
- [ ] API endpoints are correct (paths, methods, parameters)
- [ ] Technology versions match manifests
- [ ] Environment variables are correctly documented
- [ ] Code snippets are accurate
- [ ] Diagrams reflect actual architecture
- [ ] Referenced config files exist

2. Audience Value
- [ ] Appropriate for new team members
- [ ] Actionable and practical
- [ ] Right level of detail
- [ ] Clear and understandable

3. Completeness
- [ ] No significant omissions
- [ ] No unresolved TODOs that should be filled
- [ ] Terms are defined
- [ ] Cross-references are present
</checklist>

<outputFormat>
Provide findings in structured tables with:
- Location (chapter:section)
- Issue description
- Evidence from code
- Proposed fix
- Priority/Severity
</outputFormat>

<instruction>
DO NOT apply any fixes. Report findings only.
</instruction>
```
### Diagram improvement

After the verification of the Software Guidebook, propose to the user to improve the visual appearance of the diagrams. Mermaid diagrams are often a bit dull and confusing.
If the user agrees, use the 'diagram-improver' skill to execute the improvement. 

## C4 Model Diagrams

Generate Mermaid C4 diagrams. See `references/c4-mermaid.md` for syntax and examples.

### Diagram Levels

1. **Context Diagram** - System + external actors/systems
2. **Container Diagram** - High-level tech building blocks, usually sparate processes (apps, databases, queues)
3. **Component Diagram** - Components within a container, usually folder names in a folder-by-feature source hierachy.
4. **Code Diagram** - (Optional) Class/module level, usually too detailed

Ensure diagrams are accurate and directly derived from information in the relevant_source files.

### Other diagrams
EXTENSIVELY use other types of Mermaid diagrams (e.g., `flowchart TD`, `sequenceDiagram`, `classDiagram`, `erDiagram`, `graph TD`) to visually represent dynamics, flows, relationships, and schemas found in the source files.


### Classifying Internal vs External Systems

A system is **internal** if:
- It plays a relevant role in the system's functionality
- Its behavior is controlled by the development team
- The team owns and maintains the code (even if hosted externally, e.g., on AWS/Azure)

A system is **external** if:
- It is developed/maintained by another team or organization
- The team has no control over its behavior or implementation
- Examples: third-party APIs, services owned by other internal teams

## Section Guidelines

### Key Principles

- **Document the "why"** - Architecture decisions matter more than describing code (except for important aspects of the code that are particularly complex or distributed over multiple files)
- **Keep it current** - A stale guidebook is worse than none. But don't describe anything that isn't in the codebase (except for plans that explain certain choices)
- **Right level of detail** - Enough to onboard, not a line-by-line walkthrough. The entire SGB should be readable in one sitting of a few hours max.
- **Audience: new team members** - Write for someone joining tomorrow.
- **Technical Accuracy:** All information must be derived SOLELY from the files in this repository. Do not infer, invent, or use external knowledge about similar systems or common practices unless it's directly supported by the provided code. If information is not present in the provided files, do not include it or explicitly state its absence if crucial to the topic.

### Referencing 
Use the 'documentation-referencing' skill for adding lots of relevant references.

For EVERY piece of significant information, explanation, diagram, table entry, or code snippet, you MUST cite the specific source file(s) and relevant line numbers from which the information was derived.

Every significant concept, component, function, class, or configuration MUST link to:
* Its implementation in source code
* Related sections in the documentation
* Supporting documents (specs, designs, external references, research docs, manuals)

#### Reference Density
* 3-5 hyperlinks per major section minimum
* Each code concept links to its source
* Each architectural term links to its definition
* Cross-link bidirectionally: if A mentions B, B should mention A

### Tables
Use Markdown tables to summarize information such as:
*   Key features or components and their descriptions.
*   API endpoint parameters, types, and descriptions.
*   Configuration options, their types, and default values.
*   Data model fields, types, constraints, and descriptions.

### Chapter 4: Constraints

Focus **only** on constraints the team cannot modify or influence:
- Corporate/organizational policies
- Regulatory or compliance requirements
- Mandated technologies (imposed from outside the team)
- Budget or timeline constraints
- Integration requirements with systems the team doesn't control

**Do NOT include** as constraints:
- Dependencies or versions the team chose and can change
- Hardware/browser requirements (unless externally mandated)
- Port numbers, license choices
- Any technical decision within the team's control

### Code Snippets (optional))
* In the chapters "Code", "Data", "Deployment" and "Operational Support", include short, relevant code snippets (e.g., Python, Java, JavaScript, SQL, JSON, YAML) directly from the relevant source files to illustrate key implementation details, data structures, or configurations.
* Ensure snippets are well-formatted within Markdown code blocks with appropriate language identifiers.


## Remember:
- Ground every claim in the provided source files.
- Prioritize accuracy and direct representation of the code's functionality and structure.
- Structure each chapter logically for easy understanding by other developers.

## Working with Users

- **Never invent** intentions, targets, goals, or requirements. If information cannot be discovered from the codebase, ask the user.
- When asking, always offer three options:
  1. **Provide the information** now
  2. **Skip** this section/item entirely
  3. **Postpone** - insert a `TODO:` marker in the SGB for later
- Example: "What are your performance targets for API response time? You can: (1) specify targets, (2) skip this section, or (3) I'll add a TODO for later."
- Present auto-discovered content for validation
- Highlight sections marked TODO that need user input
- Offer to iterate on specific sections
