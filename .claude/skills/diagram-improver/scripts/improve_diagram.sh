#!/bin/bash

# Configuration
if [[ -z "$OPENROUTER_KEY" ]]; then
    echo "Error: OPENROUTER_KEY environment variable is not set."
    echo "Export your OpenRouter API key: export OPENROUTER_KEY='your-key-here'"
    exit 1
fi

OUTPUT_PATH="$1"
MERMAID_TEXT="$2"
RENDER_WIDTH="${3:-1200}"   # Width for rendering (default: 1200)

if [[ -z "$OUTPUT_PATH" || -z "$MERMAID_TEXT" ]]; then
    echo "Usage: $0 <output_path> \"<mermaid_text>\" [width]"
    echo "  width: Width in pixels (default: 1200)"
    exit 1
fi

# Check dependencies
for cmd in curl jq bc file python3; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# 0. Render Mermaid to Image using mermaid.ink
echo "Rendering Mermaid diagram via mermaid.ink... (${RENDER_WIDTH}px wide)"

IMAGE_PATH="temp_mermaid_$(date +%s).jpg"

# Encode diagram for mermaid.ink (pako/zlib compression + base64)
ENCODED=$(python3 -c "
import base64
import zlib
import json
import sys

diagram = '''$MERMAID_TEXT'''
data = json.dumps({'code': diagram, 'mermaid': {'theme': 'default'}})
compressed = zlib.compress(data.encode('utf-8'), 9)
encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
print(encoded)
" 2>/dev/null)

if [[ -z "$ENCODED" ]]; then
    echo "Error: Failed to encode Mermaid diagram."
    exit 1
fi

# Fetch image from mermaid.ink with width
MERMAID_INK_URL="https://mermaid.ink/img/pako:${ENCODED}?width=${RENDER_WIDTH}"

if ! curl -f -s -o "$IMAGE_PATH" "$MERMAID_INK_URL"; then
    echo "Error: Failed to render Mermaid diagram via mermaid.ink."
    echo "Falling back to Kroki..."
    
    # Fallback to Kroki (lower resolution but more reliable for some diagram types)
    IMAGE_PATH="temp_kroki_$(date +%s).png"
    if ! printf '%s' "$MERMAID_TEXT" | curl -f -s -H "Content-Type: text/plain" https://kroki.io/mermaid/png --data-binary @- -o "$IMAGE_PATH"; then
        echo "Error: Both mermaid.ink and Kroki failed to render the diagram."
        exit 1
    fi
    echo "Using Kroki fallback (standard resolution)."
fi

# Verify the image was created and is valid
if [[ ! -s "$IMAGE_PATH" ]]; then
    echo "Error: Rendered image is empty."
    exit 1
fi

# Read Prompt from file
PROMPT_FILE="$(dirname "$0")/mermaid_improvement.prompt"
if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "Error: Prompt file not found at $PROMPT_FILE"
    rm "$IMAGE_PATH"
    exit 1
fi
PROMPT_BASE=$(cat "$PROMPT_FILE")

# Escape special characters for JSON using Python
PROMPT=$(python3 -c "
import json
import sys
prompt_base = '''$PROMPT_BASE'''
mermaid_text = '''$MERMAID_TEXT'''
full_prompt = prompt_base + mermaid_text
# Output JSON-escaped string without the surrounding quotes
print(json.dumps(full_prompt)[1:-1])
")
# 1. Platform-native Resolution Detection (No 3rd-party tools)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS built-in tool
    WIDTH=$(sips -g pixelWidth "$IMAGE_PATH" | awk '/pixelWidth/ {print $2}')
    HEIGHT=$(sips -g pixelHeight "$IMAGE_PATH" | awk '/pixelHeight/ {print $2}')
else
    # Linux built-in tool (file)
    # Use -b to avoid filename in output (which might contain numbers)
    # Regex allows optional spaces around 'x' (e.g., "800 x 600" or "800x600")
    DIMENSIONS=$(file -b "$IMAGE_PATH" | grep -oE '[0-9]+ *x *[0-9]+' | head -n 1)
    # Remove spaces to handle "800 x 600" -> "800x600" for cutting
    DIMENSIONS_CLEAN=$(echo "$DIMENSIONS" | tr -d ' ')
    WIDTH=$(echo "$DIMENSIONS_CLEAN" | cut -d'x' -f1)
    HEIGHT=$(echo "$DIMENSIONS_CLEAN" | cut -d'x' -f2)
fi

if [[ -z "$WIDTH" || -z "$HEIGHT" ]]; then
    echo "Error: Could not detect image resolution."
    rm "$IMAGE_PATH"
    exit 1
fi

echo "-- Mermaid image: ${WIDTH}x${HEIGHT} pixels"

# 2. Aspect Ratio Logic for Nano Banana Pro (Supported: 1:1, 3:2, 2:3, 4:3, 3:4, 16:9, 9:16)
RATIO=$(echo "scale=2; $WIDTH / $HEIGHT" | bc)
if (( $(echo "$RATIO > 1.6" | bc -l) )); then ASPECT="16:9"
elif (( $(echo "$RATIO > 1.3" | bc -l) )); then ASPECT="3:2"
elif (( $(echo "$RATIO > 0.8" | bc -l) )); then ASPECT="1:1"
elif (( $(echo "$RATIO > 0.6" | bc -l) )); then ASPECT="2:3"
else ASPECT="9:16"
fi

# 3. Base64 Encode Input Image
MIME_TYPE=$(file --mime-type -b "$IMAGE_PATH")
# Use tr -d '\n' to ensure single line output on both Linux and macOS
BASE64_IMAGE=$(base64 < "$IMAGE_PATH" | tr -d '\n')

# 4. Request to OpenRouter (Full Correct Endpoint)
# Spec: 17cm @ 240dpi = 1606px. "2K" resolution (~2048px) fulfills this.
response=$(curl -s -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"google/gemini-3-pro-image-preview\",
    \"messages\": [
      {
        \"role\": \"user\",
        \"content\": [
          { \"type\": \"text\", \"text\": \"$PROMPT\" },
          { \"type\": \"image_url\", \"image_url\": { \"url\": \"data:$MIME_TYPE;base64,$BASE64_IMAGE\" } }
        ]
      }
    ],
    \"modalities\": [\"image\", \"text\"],
    \"image_config\": {
      \"aspect_ratio\": \"$ASPECT\",
      \"image_size\": \"2K\"
    }
  }")

# 5. Extract and Decode Base64 Image from Response
# Nano Banana Pro returns an array of image objects in the message
IMAGE_DATA=$(echo "$response" | jq -r '.choices[0].message.images[0].image_url.url')

if [[ $IMAGE_DATA == data:image* ]]; then
    echo "$IMAGE_DATA" | sed 's/data:image\/.*;base64,//' | base64 --decode > "$OUTPUT_PATH"
    echo "-- Success! Image saved as $OUTPUT_PATH (Aspect Ratio: $ASPECT)"
else
    ERROR_MSG=$(echo "$response" | jq -r '.error.message // "Unknown Error"')
    echo "Error: $ERROR_MSG"
    echo "Full response: $response"
fi

# Cleanup
rm -f "$IMAGE_PATH"
