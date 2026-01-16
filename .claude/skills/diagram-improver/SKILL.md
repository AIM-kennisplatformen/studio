---
name: diagram-improver
description: Mermaid -> PNG. Given a diagram written in Mermaid, this skill will use Nano Banana to create a visually attractive version of the diagram as a png.
context: fork
agent: general-purpose
model: haiku        
allowed-tools: Read, Write, Edit, Bash, Glob
---


# diagram-improver

## Instructions

Use this skill to improve diagrams that are written with Mermaid syntax. 

The API key must be set via the `OPENROUTER_KEY` environment variable.

## Workflow

1. Check if the environment variable OPENROUTER_KEY has a value. If not, stop with a friendly message.
1. A filename for a markdown text is provided. In that file, find all Mermaid diagrams.
2. For each mermaid diagram found:
   1. Extract the full Mermaid text of the diagram. Do not extract the markdown delimiters (e.g. ```markdown etc.)
   2. Use the improve_diagram.sh script to get an improved version of the diagram as a PNG file. The output image must be placed in the 'diagrams' subdirectory of the directory that holds the markdown file.
    When processing multiple diagrams, launch all improve_diagram.sh invocations in parallel by making multiple Bash tool calls in a single response, each with `run_in_background: true`.
   3. Add the image(s) to the markdown file, immediately after the corresponding Mermaid version of the diagram, and replacing an earlier image version of the diagram. DO NOT remove the original Mermaid diagram.
   2. In the markdown file, place the Mermaid version in a html details section, like this:
	<details>
	   <summary>original mermaid diagram</summary>
	   ```mermaid
	   [MERMAID SOURCE TEXT]
	   ```
	</details>   

## Script invocation

Usage:
```bash
./improve_diagram.sh <output_path> "<mermaid_text>" [width]
```

Use 1200 for the width argument.

Example: 
```bash
./improve_diagram.sh "output/diagram.png" 'sequenceDiagram
    participant A as Alice
    participant B as Bob
    A->>B: Hello Bob!
    B-->>A: Hi Alice!' 1200
```

### Set your API key:
```bash
export OPENROUTER_KEY="your-api-key-here"
```
