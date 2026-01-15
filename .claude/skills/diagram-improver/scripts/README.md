# improve_diagram.sh

Converts a Mermaid diagram to a visually enhanced PNG image using AI-powered image generation.

## Prerequisites

Set the `OPENROUTER_KEY` environment variable with your OpenRouter API key:

```bash
export OPENROUTER_KEY='your-openrouter-api-key'
```

## Usage

```bash
./improve_diagram.sh <output_path> "<mermaid_text>" [width]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `output_path` | Yes | — | Path for the output PNG file |
| `mermaid_text` | Yes | — | Mermaid diagram code (quoted string) |
| `width` | No | 1200 | Width in pixels |

<details>
<summary>Dependencies</summary>

- `curl` - HTTP requests
- `jq` - JSON parsing
- `bc` - Math calculations
- `file` - MIME type detection
- `python3` - Encoding and JSON handling

</details>

<details>
<summary>Examples</summary>

Basic usage:

```bash
./improve_diagram.sh "output/diagram.png" 'sequenceDiagram
    participant A as Alice
    participant B as Bob
    A->>B: Hello Bob!
    B-->>A: Hi Alice!'
```

With custom width:

```bash
./improve_diagram.sh "output/diagram.png" '<mermaid_code>' 1600
```

</details>

<details>
<summary>How it Works</summary>

1. Renders Mermaid to image via mermaid.ink (fallback: Kroki)
2. Detects aspect ratio and selects matching ratio (1:1, 3:2, 2:3, 16:9, 9:16)
3. Sends to Gemini via OpenRouter API for visual enhancement
4. Outputs a 2K resolution PNG image

</details>
