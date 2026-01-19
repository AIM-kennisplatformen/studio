#!/bin/bash
# GitHub Issue Management Tool - Consolidated BMAD Issue Management Scripts
# Manages GitHub issues, project boards, and issue relationships for BMAD workflows

VERSION="1.0.0"
SCRIPT_NAME="github-issue-manager.sh"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables (will be set by load_config)
REPO=""
REPO_OWNER=""
REPO_NAME=""
BOARD_ID=""
CONFIG_FILE=""
PROJECT_ROOT=""
PROJECT_ID=""
PROJECT_NUMBER=""
STATUS_FIELD_ID=""
BACKLOG_OPTION_ID=""

#=============================================================================
# UTILITY FUNCTIONS
#=============================================================================

print_usage() {
    cat << EOF
GitHub Issue Manager v${VERSION}

USAGE:
    ${SCRIPT_NAME} <command> [options]

COMMANDS:
    create-epic <title> <body> <epic_slug>
        Create epic issue with required slug for labeling.

    create-sub-epic <title> <body> <sub_epic_slug> --parent <parent_epic_num> <parent_epic_slug>
        Create sub-epic issue linked as a sub-issue of a parent epic.

    create-story <title> <body> <story_slug> [--epic <epic_num> <epic_slug>]
        Create story issue. Story slug is always required.
        Use --epic to link to a parent epic (requires both epic number and slug).

    create-task <title> <body> [--story <story_num> <story_slug>] [--epic-slug <epic_slug>]
        Create task issue. Use --story to link to a parent story.
        Use --epic-slug to add epic label without linking.

    update-status <issue_num> <status>
        Update issue status on project board.

    list-stories [filter]
        List stories (default: "label:story state:open")

    migrate-stories
        Migrate Markdown stories to GitHub issues.

    get-story-context <issue_num>
        Get comprehensive context for a user story.

    help                Show this help message
    version             Show version information

EXAMPLES:
    # Create an epic
    ${SCRIPT_NAME} create-epic "Epic 1: Foundation" "Setup basic infrastructure" "foundation"

    # Create a sub-epic linked to a parent epic
    ${SCRIPT_NAME} create-sub-epic "Sub-Epic: Database Layer" "Database infrastructure setup" "db-layer" --parent 15 "foundation"

    # Create a story linked to an epic
    ${SCRIPT_NAME} create-story "User Auth" "As a user I want to login" "user-auth" --epic 15 "foundation"

    # Create a standalone story (no epic)
    ${SCRIPT_NAME} create-story "Bug Fix" "Fix login timeout issue" "login-fix"

    # Create a task linked to a story
    ${SCRIPT_NAME} create-task "Login form validation" "Implement client-side validation" --story 16 "user-auth"

    # Create a task with epic label only (no story link)
    ${SCRIPT_NAME} create-task "Setup CI pipeline" "Configure GitHub Actions" --epic-slug "foundation"

    # Create a standalone task
    ${SCRIPT_NAME} create-task "Quick fix" "Patch security issue"

    # Other commands
    ${SCRIPT_NAME} update-status 42 "In Progress"
    ${SCRIPT_NAME} list-stories
    ${SCRIPT_NAME} migrate-stories
    ${SCRIPT_NAME} get-story-context 42

For detailed usage examples, see: README github-issue-manager.md
Slug creation tips: derive from title, lowercase, hyphens instead of spaces, alphanumeric and hyphens only, max 20 characters, use well known abbreviations where possible (e.g., "auth" for "authentication"), avoid stop words (e.g., "the", "and", "of")
EOF
}

print_version() {
    echo "${SCRIPT_NAME} v${VERSION}"
    echo "Consolidated GitHub Issue Management for BMAD workflows"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

output_json() {
    echo "$1"
}

output_error() {
    echo "{\"error\": \"$1\"}" >&2
    exit 1
}

# Cache for existing labels to avoid redundant API calls (bash 3.x compatible)
# Uses a newline-separated string instead of associative arrays
LABEL_CACHE=""

# Check if label exists (uses cache)
label_exists() {
    local label_name="$1"

    # Check cache first (grep for exact match with delimiters)
    if echo "$LABEL_CACHE" | grep -qFx "$label_name"; then
        return 0
    fi

    # Query GitHub API
    if gh label list --repo "$REPO" --json name 2>/dev/null | jq -e --arg name "$label_name" '.[] | select(.name == $name)' >/dev/null 2>&1; then
        # Add to cache
        LABEL_CACHE="${LABEL_CACHE}${label_name}"$'\n'
        return 0
    else
        return 1
    fi
}

# Validate that a slug is not purely numeric (common AI agent mistake)
validate_slug() {
    local slug="$1"
    local slug_type="$2"  # "epic" or "story" for error messages
    
    # Allow empty slugs (they're handled elsewhere)
    if [ -z "$slug" ]; then
        return 0
    fi
    
    # Reject purely numeric slugs - this is likely an issue number passed by mistake
    if [[ "$slug" =~ ^[0-9]+$ ]]; then
        log_warning "Invalid ${slug_type}_slug: '$slug' appears to be an issue number, not a semantic slug."
        log_warning "Slugs should be descriptive (e.g., 'user-auth', 'foundation') not issue numbers."
        log_warning "Check that you're passing the correct parameters to the script."
        output_error "Invalid ${slug_type}_slug: '$slug'. Slugs must contain at least one letter or hyphen, not be purely numeric. Expected format: 'lowercase-hyphenated-slug'"
    fi
    
    return 0
}

# Create label if it doesn't exist
ensure_label() {
    local label_name="$1"
    local description="$2"
    local color="$3"

    if ! label_exists "$label_name"; then
        if gh label create "$label_name" --description "$description" --color "$color" --repo "$REPO" 2>/dev/null; then
            # Add to cache on successful creation
            LABEL_CACHE="${LABEL_CACHE}${label_name}"$'\n'
        fi
    fi
}

check_dependencies() {
    local missing_deps=()
    
    if ! command -v yq &> /dev/null; then
        missing_deps+=("yq (install with: brew install yq)")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq (install with: brew install jq)")
    fi
    
    if ! command -v gh &> /dev/null; then
        missing_deps+=("gh (install with: brew install gh)")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            log_error "  - $dep"
        done
        exit 1
    fi
    
    # Check GitHub authentication
    if ! gh auth status &> /dev/null; then
        output_error "GitHub CLI not authenticated. Run: gh auth login"
    fi
}

#=============================================================================
# CONFIGURATION FUNCTIONS
#=============================================================================

load_config() {
    check_dependencies
    
    # Find project root by looking for .bmad-core directory
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$script_dir" && while [[ ! -d ".bmad-core" && "$(pwd)" != "/" ]]; do cd ..; done && pwd)"
    
    if [[ ! -d "$PROJECT_ROOT/.bmad-core" ]]; then
        output_error "Could not find project root with .bmad-core directory"
    fi
    
    CONFIG_FILE="$PROJECT_ROOT/.bmad-core/core-config.yaml"
    if [[ ! -f "$CONFIG_FILE" ]]; then
        output_error "core-config.yaml not found at $CONFIG_FILE"
    fi
    
    # Load repo configuration
    REPO=$(yq eval '.github.repo' "$CONFIG_FILE" 2>/dev/null || echo "")
    if [ -z "$REPO" ] || [ "$REPO" = "null" ]; then
        output_error "No github.repo configured in core-config.yaml"
    fi
    
    # Validate repo format (owner/repo)
    if [[ ! "$REPO" =~ ^[^/]+/[^/]+$ ]]; then
        output_error "Invalid repo format. Expected: owner/repo, got: $REPO"
    fi
    
    REPO_OWNER=$(echo "$REPO" | cut -d'/' -f1)
    REPO_NAME=$(echo "$REPO" | cut -d'/' -f2)
    
    # Validate owner and name are not empty
    if [ -z "$REPO_OWNER" ] || [ -z "$REPO_NAME" ]; then
        output_error "Failed to parse repo owner/name from: $REPO"
    fi
    
    BOARD_ID=$(yq eval '.github.project_board' "$CONFIG_FILE" 2>/dev/null || echo "")
    # Board ID can be empty (will be created by ensure_project_board)
    
}

#=============================================================================
# PROJECT BOARD FUNCTIONS
#=============================================================================

ensure_project_board() {
    if [ -z "$REPO" ]; then
        load_config
    fi
    
    # Get organization project board title from config
    local project_name=$(yq eval '.github.project_board' "$CONFIG_FILE" 2>/dev/null || echo "")
    if [ -z "$project_name" ] || [ "$project_name" = "null" ]; then
        output_error "project_board is not configured in core-config.yaml"
    fi
    
    log_info "Looking for project board with title: $project_name"
    
    # Check if project exists (using new Projects API)
    local project_exists=false
    PROJECT_ID=""
    PROJECT_NUMBER=""
    
    # List organization projects to find existing one
    local projects_response=$(gh project list --owner "$REPO_OWNER" --format json 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$projects_response" ]; then
        local existing_project=$(echo "$projects_response" | jq -r --arg name "$project_name" '.projects[] | select(.title == $name) // empty')
        if [ -n "$existing_project" ] && [ "$existing_project" != "null" ]; then
            PROJECT_ID=$(echo "$existing_project" | jq -r '.id // empty')
            PROJECT_NUMBER=$(echo "$existing_project" | jq -r '.number // empty')
            if [ -n "$PROJECT_ID" ] && [ -n "$PROJECT_NUMBER" ]; then
                project_exists=true
                log_info "Found existing project: $project_name (Number: $PROJECT_NUMBER, ID: $PROJECT_ID)"
            fi
        fi
    fi
    
    if [ "$project_exists" = false ]; then
        log_info "Project '$project_name' not found. Creating new project..."
        # Create new project (v2)
        local create_response=$(gh project create --owner "$REPO_OWNER" --title "$project_name" --format json 2>&1)
        
        if [ $? -ne 0 ] || [ -z "$create_response" ]; then
            output_error "Failed to create project: $create_response"
        fi
        
        # Parse response
        PROJECT_ID=$(echo "$create_response" | jq -r '.id // empty')
        PROJECT_NUMBER=$(echo "$create_response" | jq -r '.number // empty')
        
        if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "null" ] || [ -z "$PROJECT_NUMBER" ] || [ "$PROJECT_NUMBER" = "null" ]; then
            output_error "Failed to parse project ID/number from response"
        fi
        
        log_success "Project created: $project_name (ID: $PROJECT_ID, Number: $PROJECT_NUMBER)"
    else
        log_info "Using existing project: $project_name (ID: $PROJECT_ID, Number: $PROJECT_NUMBER)"
    fi
    
    # Get project fields to find the existing Status field
    local fields_response=$(gh project field-list "$PROJECT_NUMBER" --owner "$REPO_OWNER" --format json 2>/dev/null)
    STATUS_FIELD_ID=""
    
    if [ $? -eq 0 ] && [ -n "$fields_response" ]; then
        # Extract Status field info including existing options
        local status_field_info=$(echo "$fields_response" | jq -r '.fields[] | select(.name == "Status")')
        if [ -n "$status_field_info" ] && [ "$status_field_info" != "null" ]; then
            STATUS_FIELD_ID=$(echo "$status_field_info" | jq -r '.id // empty')
            local existing_options=$(echo "$status_field_info" | jq -r '.options[]?.name // empty' | tr '\n' ',' | sed 's/,$//')
            log_info "Status field exists with ID: $STATUS_FIELD_ID"
            log_info "Existing options: $existing_options"
        fi
    fi
    
    if [ -z "$STATUS_FIELD_ID" ] || [ "$STATUS_FIELD_ID" = "null" ]; then
        output_error "Status field not found in project"
    fi

    # Get the Backlog option ID for setting initial status
    BACKLOG_OPTION_ID=$(gh api graphql -f query='
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      fields(first: 20) {
        nodes {
          ... on ProjectV2SingleSelectField {
            id
            name
            options {
              id
              name
            }
          }
        }
      }
    }
  }
}' -f projectId="$PROJECT_ID" 2>/dev/null | jq -r '.data.node.fields.nodes[] | select(.name == "Status") | .options[] | select(.name == "Backlog") | .id // empty')

    if [ -n "$BACKLOG_OPTION_ID" ] && [ "$BACKLOG_OPTION_ID" != "null" ]; then
        log_info "Backlog option ID: $BACKLOG_OPTION_ID"
    else
        log_warning "Could not find Backlog option ID, status setting will be skipped"
    fi

    # Link repository to project
    log_info "Linking repository to project..."
    gh project link "$PROJECT_NUMBER" --owner "$REPO_OWNER" --repo "$REPO" 2>/dev/null
    # Don't fail if already linked
    
}

#=============================================================================
# ISSUE CREATION FUNCTIONS
#=============================================================================

create_epic_issue() {
    local title="$1"
    local body="$2"
    local epic_slug="$3"
    
    if [ -z "$title" ] || [ -z "$body" ] || [ -z "$epic_slug" ]; then
        output_error "Usage: create-epic <title> <body> <epic_slug>"
    fi
    
    # Validate slug is not purely numeric (common AI agent mistake - passing issue numbers as slugs)
    validate_slug "$epic_slug" "epic"
    
    if [ -z "$REPO" ]; then
        load_config
    fi

    ensure_project_board

    # Create epic label if it doesn't exist
    ensure_label "epic:$epic_slug" "Epic stories" "1e3a8a"

    # Create issue and capture the issue number directly
    local issue_url=$(gh issue create --repo "$REPO" --title "$title" --body "$body" --label "epic,epic:$epic_slug")
    if [ $? -ne 0 ]; then
        output_error "Failed to create epic issue"
    fi
    
    local epic_num=$(echo "$issue_url" | grep -o '[0-9]*$')
    if [ -z "$epic_num" ]; then
        output_error "Failed to parse epic issue number"
    fi
    
    # Add to project and set status to Backlog
    log_info "Adding epic to project..."
    local add_response=$(gh project item-add "$PROJECT_NUMBER" --owner "$REPO_OWNER" --url "https://github.com/$REPO/issues/$epic_num" --format json 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$add_response" ]; then
        local epic_item_id=$(echo "$add_response" | jq -r '.id // empty')
        if [ -n "$epic_item_id" ] && [ "$epic_item_id" != "null" ]; then
            # Set status to Backlog using the option ID
            if [ -n "$BACKLOG_OPTION_ID" ] && [ "$BACKLOG_OPTION_ID" != "null" ]; then
                gh project item-edit --id "$epic_item_id" --project-id "$PROJECT_ID" --field-id "$STATUS_FIELD_ID" --single-select-option-id "$BACKLOG_OPTION_ID" 2>/dev/null
                if [ $? -eq 0 ]; then
                    log_success "Epic added to project with Backlog status"
                else
                    log_warning "Epic added to project but failed to set status"
                fi
            else
                log_warning "Epic added to project (status not set - no Backlog option ID)"
            fi
        else
            log_warning "Epic added to project but failed to parse item ID"
        fi
    else
        log_warning "Failed to add epic to project, manual addition needed"
    fi

    output_json "{\"epic_number\": $epic_num}"
}

create_sub_epic_issue() {
    # Parameters: title, body, sub_epic_slug, parent_epic_num, parent_epic_slug
    local title="$1"
    local body="$2"
    local sub_epic_slug="$3"
    local parent_epic_num="$4"
    local parent_epic_slug="$5"
    
    # Validate required parameters
    if [ -z "$title" ] || [ -z "$body" ] || [ -z "$sub_epic_slug" ]; then
        output_error "Usage: create-sub-epic <title> <body> <sub_epic_slug> --parent <parent_epic_num> <parent_epic_slug>"
    fi
    
    # Parent epic info is required for sub-epics
    if [ -z "$parent_epic_num" ] || [ -z "$parent_epic_slug" ]; then
        output_error "Sub-epic requires --parent <parent_epic_num> <parent_epic_slug>"
    fi
    
    # Validate slugs are not purely numeric
    validate_slug "$sub_epic_slug" "sub-epic"
    validate_slug "$parent_epic_slug" "parent-epic"
    
    # Validate parent_epic_num is numeric
    if ! [[ "$parent_epic_num" =~ ^[0-9]+$ ]]; then
        output_error "Invalid parent_epic_num: $parent_epic_num. Must be numeric."
    fi
    
    if [ -z "$REPO" ]; then
        load_config
    fi

    ensure_project_board
    
    # Enhance body with parent epic reference
    local enhanced_body="$body

Parent Epic: $parent_epic_slug (#$parent_epic_num)"

    # Create labels - sub-epic gets both its own epic label and parent's epic label
    ensure_label "epic:$sub_epic_slug" "Sub-epic stories" "1e3a8a"
    ensure_label "epic:$parent_epic_slug" "Epic $parent_epic_num stories" "1e3a8a"
    local labels="epic,epic:$sub_epic_slug,epic:$parent_epic_slug"

    # Create sub-epic issue
    local issue_url=$(gh issue create --repo "$REPO" --title "$title" --body "$enhanced_body" --label "$labels")
    if [ $? -ne 0 ]; then
        output_error "Failed to create sub-epic issue"
    fi
    
    local sub_epic_num=$(echo "$issue_url" | grep -o '[0-9]*$')
    if [ -z "$sub_epic_num" ]; then
        output_error "Failed to parse sub-epic issue number"
    fi
    
    # Add to project and set status to Backlog
    log_info "Adding sub-epic to project..."
    local add_response=$(gh project item-add "$PROJECT_NUMBER" --owner "$REPO_OWNER" --url "https://github.com/$REPO/issues/$sub_epic_num" --format json 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$add_response" ]; then
        local sub_epic_item_id=$(echo "$add_response" | jq -r '.id // empty')
        if [ -n "$sub_epic_item_id" ] && [ "$sub_epic_item_id" != "null" ]; then
            if [ -n "$BACKLOG_OPTION_ID" ] && [ "$BACKLOG_OPTION_ID" != "null" ]; then
                gh project item-edit --id "$sub_epic_item_id" --project-id "$PROJECT_ID" --field-id "$STATUS_FIELD_ID" --single-select-option-id "$BACKLOG_OPTION_ID" 2>/dev/null
                if [ $? -eq 0 ]; then
                    log_success "Sub-epic added to project with Backlog status"
                else
                    log_warning "Sub-epic added to project but failed to set status"
                fi
            else
                log_warning "Sub-epic added to project (status not set - no Backlog option ID)"
            fi
        else
            log_warning "Sub-epic added to project but failed to parse item ID"
        fi
    else
        log_warning "Failed to add sub-epic to project, manual addition needed"
    fi

    # Create sub-issue relationship with parent epic
    create_sub_issue_relationship "$parent_epic_num" "$sub_epic_num"
    
    output_json "{\"sub_epic_number\": $sub_epic_num, \"parent_epic_number\": $parent_epic_num}"
}

create_story_issue() {
    # Parameters: title, body, story_slug, [epic_num], [epic_slug]
    # epic_num and epic_slug are optional but must be provided together
    local title="$1"
    local body="$2"
    local story_slug="$3"
    local epic_num="$4"
    local epic_slug="$5"
    
    # Validate required parameters
    if [ -z "$title" ] || [ -z "$body" ] || [ -z "$story_slug" ]; then
        output_error "Usage: create-story <title> <body> <story_slug> [--epic <epic_num> <epic_slug>]"
    fi
    
    # Validate slugs are not purely numeric (common AI agent mistake - passing issue numbers as slugs)
    validate_slug "$story_slug" "story"
    
    # If epic_num is provided, epic_slug must also be provided (and vice versa)
    if [ -n "$epic_num" ] && [ -z "$epic_slug" ]; then
        output_error "When providing --epic, both <epic_num> and <epic_slug> are required"
    fi
    if [ -n "$epic_slug" ] && [ -z "$epic_num" ]; then
        output_error "When providing --epic, both <epic_num> and <epic_slug> are required"
    fi
    
    # Validate epic_num is numeric if provided
    if [ -n "$epic_num" ] && ! [[ "$epic_num" =~ ^[0-9]+$ ]]; then
        output_error "Invalid epic_num: $epic_num. Must be numeric."
    fi
    
    if [ -n "$epic_slug" ]; then
        validate_slug "$epic_slug" "epic"
    fi
    
    if [ -z "$REPO" ]; then
        load_config
    fi

    ensure_project_board
    
    # Enhance body with parent epic reference (only if epic info provided)
    local enhanced_body="$body"
    if [ -n "$epic_num" ] && [ -n "$epic_slug" ]; then
        enhanced_body="$body

Parent Epic: $epic_slug (#$epic_num)"
    fi
    
    # Create labels
    local labels="story"
    if [ -n "$epic_slug" ]; then
        ensure_label "epic:$epic_slug" "Epic $epic_num stories" "1e3a8a"
        labels="$labels,epic:$epic_slug"
    fi
    ensure_label "story:$story_slug" "Story $story_slug" "9017ca"
    labels="$labels,story:$story_slug"

    # Create story issue and capture the issue number directly
    local issue_url=$(gh issue create --repo "$REPO" --title "$title" --body "$enhanced_body" --label "$labels")
    if [ $? -ne 0 ]; then
        output_error "Failed to create story issue"
    fi
    
    local story_num=$(echo "$issue_url" | grep -o '[0-9]*$')
    if [ -z "$story_num" ]; then
        output_error "Failed to parse story issue number"
    fi
    
    # Add to project and set status to Backlog
    log_info "Adding story to project..."
    local add_response=$(gh project item-add "$PROJECT_NUMBER" --owner "$REPO_OWNER" --url "https://github.com/$REPO/issues/$story_num" --format json 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$add_response" ]; then
        local story_item_id=$(echo "$add_response" | jq -r '.id // empty')
        if [ -n "$story_item_id" ] && [ "$story_item_id" != "null" ]; then
            # Set status to Backlog using the option ID
            if [ -n "$BACKLOG_OPTION_ID" ] && [ "$BACKLOG_OPTION_ID" != "null" ]; then
                gh project item-edit --id "$story_item_id" --project-id "$PROJECT_ID" --field-id "$STATUS_FIELD_ID" --single-select-option-id "$BACKLOG_OPTION_ID" 2>/dev/null
                if [ $? -eq 0 ]; then
                    log_success "Story added to project with Backlog status"
                else
                    log_warning "Story added to project but failed to set status"
                fi
            else
                log_warning "Story added to project (status not set - no Backlog option ID)"
            fi
        else
            log_warning "Story added to project but failed to parse item ID"
        fi
    else
        log_warning "Failed to add story to project, manual addition needed"
    fi

    # Create sub-issue relationship with epic (only if epic_num exists)
    if [ -n "$epic_num" ]; then
        create_sub_issue_relationship "$epic_num" "$story_num"
    fi
    
    output_json "{\"story_number\": $story_num}"
}

create_task_issue() {
    # Parameters: title, body, [story_num], [story_slug], [epic_slug]
    # story_num and story_slug must be provided together if linking to a story
    local title="$1"
    local body="$2"
    local story_num="$3"
    local story_slug="$4"
    local epic_slug="$5"
    
    # Validate required parameters
    if [ -z "$title" ] || [ -z "$body" ]; then
        output_error "Usage: create-task <title> <body> [--story <story_num> <story_slug>] [--epic-slug <epic_slug>]"
    fi
    
    # If story_num is provided, story_slug must also be provided (and vice versa)
    if [ -n "$story_num" ] && [ -z "$story_slug" ]; then
        output_error "When providing --story, both <story_num> and <story_slug> are required"
    fi
    if [ -n "$story_slug" ] && [ -z "$story_num" ]; then
        output_error "When providing --story, both <story_num> and <story_slug> are required"
    fi
    
    # Validate story_num is numeric if provided
    if [ -n "$story_num" ] && ! [[ "$story_num" =~ ^[0-9]+$ ]]; then
        output_error "Invalid story_num: $story_num. Must be numeric."
    fi
    
    # Validate slugs are not purely numeric (common AI agent mistake - passing issue numbers as slugs)
    if [ -n "$epic_slug" ]; then
        validate_slug "$epic_slug" "epic"
    fi
    if [ -n "$story_slug" ]; then
        validate_slug "$story_slug" "story"
    fi
    
    if [ -z "$REPO" ]; then
        load_config
    fi

    ensure_project_board
    
    # Build enhanced body
    local enhanced_body="$body"
    
    # Add parent story reference if provided
    if [ -n "$story_num" ]; then
        enhanced_body="$enhanced_body

Parent Story: #$story_num"
        if [ -n "$story_slug" ]; then
            enhanced_body="$enhanced_body
Story Slug: $story_slug"
        fi
    fi
    
    # Add epic slug info if provided
    if [ -n "$epic_slug" ]; then
        enhanced_body="$enhanced_body
Epic Slug: $epic_slug"
    fi

    # Create labels
    local labels="task"
    if [ -n "$epic_slug" ]; then
        ensure_label "epic:$epic_slug" "Epic $epic_slug tasks" "1e3a8a"
        labels="$labels,epic:$epic_slug"
    fi
    if [ -n "$story_slug" ]; then
        ensure_label "story:$story_slug" "Story $story_slug tasks" "9017ca"
        labels="$labels,story:$story_slug"
    fi
    
    # Create task issue and capture the issue number directly
    local issue_url=$(gh issue create --repo "$REPO" --title "$title" --body "$enhanced_body" --label "$labels")
    if [ $? -ne 0 ]; then
        output_error "Failed to create task issue"
    fi
    
    local task_num=$(echo "$issue_url" | grep -o '[0-9]*$')
    if [ -z "$task_num" ]; then
        output_error "Failed to parse task issue number"
    fi
    
    # Add to project and set status to Backlog
    log_info "Adding task to project..."
    local add_response=$(gh project item-add "$PROJECT_NUMBER" --owner "$REPO_OWNER" --url "https://github.com/$REPO/issues/$task_num" --format json 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$add_response" ]; then
        local task_item_id=$(echo "$add_response" | jq -r '.id // empty')
        if [ -n "$task_item_id" ] && [ "$task_item_id" != "null" ]; then
            # Set status to Backlog using the option ID
            if [ -n "$BACKLOG_OPTION_ID" ] && [ "$BACKLOG_OPTION_ID" != "null" ]; then
                gh project item-edit --id "$task_item_id" --project-id "$PROJECT_ID" --field-id "$STATUS_FIELD_ID" --single-select-option-id "$BACKLOG_OPTION_ID" 2>/dev/null
                if [ $? -eq 0 ]; then
                    log_success "Task added to project with Backlog status"
                else
                    log_warning "Task added to project but failed to set status"
                fi
            else
                log_warning "Task added to project (status not set - no Backlog option ID)"
            fi
        else
            log_warning "Task added to project but failed to parse item ID"
        fi
    else
        log_warning "Failed to add task to project, manual addition needed"
    fi

    # Create sub-issue relationship with parent story (only if story_num provided)
    if [ -n "$story_num" ]; then
        create_sub_issue_relationship "$story_num" "$task_num"
    fi
    
    output_json "{\"task_number\": $task_num}"
}

create_sub_issue_relationship() {
    local parent_issue_num="$1"
    local child_issue_num="$2"
    
    if [ -z "$parent_issue_num" ] || [ -z "$child_issue_num" ]; then
        output_error "Usage: create-relationship <parent_issue_num> <child_issue_num>"
    fi
    
    # Validate inputs
    if ! [[ "$parent_issue_num" =~ ^[0-9]+$ ]]; then
        output_error "Invalid parent issue number: $parent_issue_num. Must be numeric."
    fi
    
    if ! [[ "$child_issue_num" =~ ^[0-9]+$ ]]; then
        output_error "Invalid child issue number: $child_issue_num. Must be numeric."
    fi
    
    if [ -z "$REPO" ]; then
        load_config
    fi
    
    # Verify both issues exist
    if ! gh issue view "$parent_issue_num" --repo "$REPO" >/dev/null 2>&1; then
        output_error "Parent issue #$parent_issue_num not found in repo $REPO"
    fi
    
    if ! gh issue view "$child_issue_num" --repo "$REPO" >/dev/null 2>&1; then
        output_error "Child issue #$child_issue_num not found in repo $REPO"
    fi
    
    # Get issue node IDs for GraphQL
    local parent_node_id=$(gh api "repos/$REPO/issues/$parent_issue_num" --jq '.node_id' 2>/dev/null)
    local child_node_id=$(gh api "repos/$REPO/issues/$child_issue_num" --jq '.node_id' 2>/dev/null)
    
    if [ -z "$parent_node_id" ] || [ -z "$child_node_id" ]; then
        output_error "Failed to get issue node IDs"
    fi
    
    # Create sub-issue relationship using GraphQL
    log_info "Creating sub-issue relationship: #$parent_issue_num -> #$child_issue_num"
    
    local mutation_result=$(gh api graphql -f query='
      mutation($parentId: ID!, $subIssueId: ID!) {
        addSubIssue(input: {
          issueId: $parentId,
          subIssueId: $subIssueId
        }) {
          issue {
            id
            number
          }
          subIssue {
            id
            number
          }
        }
      }' -f parentId="$parent_node_id" -f subIssueId="$child_node_id" 2>&1)
    
    if [ $? -eq 0 ]; then
        # GraphQL mutation succeeded
        output_json "{\"success\": \"Sub-issue relationship created\", \"parent\": \"$parent_issue_num\", \"child\": \"$child_issue_num\"}"
    else
        # Check if it's an API error we can handle
        if echo "$mutation_result" | grep -q "not found\|does not exist"; then
            output_error "GitHub sub-issue API not available or issues not found"
        else
            output_error "Failed to create sub-issue relationship: $mutation_result"
        fi
    fi
}

#=============================================================================
# ISSUE MANAGEMENT FUNCTIONS
#=============================================================================

update_issue_status() {
    local issue_num="$1"
    local column="$2"
    
    if [ -z "$issue_num" ] || [ -z "$column" ]; then
        output_error "Usage: update-status <issue_num> <status>"
    fi
    
    # Validate inputs
    if ! [[ "$issue_num" =~ ^[0-9]+$ ]]; then
        output_error "Invalid issue number: $issue_num. Must be numeric."
    fi
    
    if [ -z "$REPO" ]; then
        load_config
    fi

    ensure_project_board
    
    # Verify issue exists
    if ! gh issue view "$issue_num" --repo "$REPO" >/dev/null 2>&1; then
        output_error "Issue #$issue_num not found in repo $REPO"
    fi
    
    # Map old column names to new status options for backward compatibility
    local status_value
    case "$column" in
        "Backlog"|"Todo"|"Next Milestone")
            status_value="Backlog"
            ;;
        "Ready")
            status_value="Ready"
            ;;    
        "In Progress")
            status_value="In Progress"
            ;;
        "AI Review")
            status_value="AI Review"
            ;;
        "Review")
            status_value="Review"
            ;;
        "Done")
            status_value="Done"
            ;;
        *)
            output_error "Invalid status: $column. Available: Backlog, Ready, In Progress, AI Review, Review, Done (or legacy: Todo, Next Milestone)"
            ;;
    esac
    
    # Check if issue is already in the project
    local issue_items_response=$(gh project item-list "$PROJECT_NUMBER" --owner "$REPO_OWNER" --format json 2>/dev/null)
    local issue_item_id=""
    
    if [ $? -eq 0 ] && [ -n "$issue_items_response" ]; then
        # Find the project item for this issue
        issue_item_id=$(echo "$issue_items_response" | jq -r --arg issue "$issue_num" --arg repo "$REPO" '[.items[] | select(.content.type == "Issue" and .content.repository == $repo and (.content.number | tostring) == $issue)] | .[0].id // empty')
    fi
    
    # Add issue to project if not already there
    if [ -z "$issue_item_id" ] || [ "$issue_item_id" = "null" ]; then
        log_info "Adding issue to project..."
        local add_response=$(gh project item-add "$PROJECT_NUMBER" --owner "$REPO_OWNER" --url "https://github.com/$REPO/issues/$issue_num" --format json 2>&1)
        
        if [ $? -ne 0 ]; then
            output_error "Failed to add issue to project: $add_response"
        fi
        
        issue_item_id=$(echo "$add_response" | jq -r '.id // empty')
        if [ -z "$issue_item_id" ] || [ "$issue_item_id" = "null" ]; then
            output_error "Failed to parse item ID from add response"
        fi
    fi
    
    # Get the option ID for the status value
    local status_option_id=$(gh api graphql -f query='
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      fields(first: 20) {
        nodes {
          ... on ProjectV2SingleSelectField {
            id
            name
            options {
              id
              name
            }
          }
        }
      }
    }
  }
}' -f projectId="$PROJECT_ID" | jq -r --arg status "$status_value" '.data.node.fields.nodes[] | select(.name == "Status") | .options[] | select(.name == $status) | .id // empty')

    if [ -z "$status_option_id" ] || [ "$status_option_id" = "null" ]; then
        output_error "Failed to find option ID for status: $status_value"
    fi

    # Update the Status field for this issue
    log_info "Setting status to: $status_value (from $column)"
    local update_response=$(gh project item-edit --id "$issue_item_id" --project-id "$PROJECT_ID" --field-id "$STATUS_FIELD_ID" --single-select-option-id "$status_option_id" 2>&1)
    
    if [ $? -eq 0 ]; then
        output_json "{\"success\": \"Issue status updated to $status_value\", \"item_id\": \"$issue_item_id\", \"original_column\": \"$column\"}"
    else
        output_error "Failed to update status: $update_response"
    fi
}

list_stories() {
    local filter=${1:-"label:story state:open"}
    
    if [ -z "$REPO" ]; then
        load_config
    fi
    
    # Parse filter into gh issue list arguments
    local gh_args=""
    if [[ "$filter" == *"label:"* ]]; then
        local label=$(echo "$filter" | sed -n 's/.*label:\([^ ]*\).*/\1/p')
        if [ -n "$label" ]; then
            gh_args="$gh_args --label \"$label\""
        fi
    fi
    
    if [[ "$filter" == *"state:"* ]]; then
        local state=$(echo "$filter" | sed -n 's/.*state:\([^ ]*\).*/\1/p')
        if [ -n "$state" ]; then
            gh_args="$gh_args --state \"$state\""
        fi
    fi
    
    # If no specific args parsed, use default
    if [ -z "$gh_args" ]; then
        gh_args="--label story --state open"
    fi
    
    # List issues
    local output=$(eval "gh issue list $gh_args --json number,title,body,labels,assignees,milestone --limit 50 --repo \"$REPO\"" 2>&1)
    if [ $? -ne 0 ]; then
        output_error "Failed to list issues: $output"
    fi
    
    # Validate JSON output
    if ! echo "$output" | jq . >/dev/null 2>&1; then
        output_error "Invalid JSON response from gh issue list"
    fi
    
    # Check if output is empty array (this is normal, not an error)
    local story_count=$(echo "$output" | jq '. | length')
    if [ "$story_count" -eq 0 ]; then
        output_json "{\"result\": [], \"count\": 0, \"message\": \"No stories found matching filter: $filter\"}"
        return 0
    fi
    
    # Return successful result with metadata
    echo "$output" | jq --arg filter "$filter" --arg count "$story_count" '. + [{"_metadata": {"filter": $filter, "count": ($count | tonumber)}}]'
}

get_story_context() {
    local issue_num="$1"
    
    if [ -z "$issue_num" ]; then
        output_error "Usage: get-story-context <issue_num>"
    fi
    
    # Validate issue number
    if ! [[ "$issue_num" =~ ^[0-9]+$ ]]; then
        output_error "Invalid issue number: $issue_num. Must be numeric."
    fi
    
    if [ -z "$REPO" ]; then
        load_config
    fi
    
    # Verify issue exists and get comprehensive data
    log_info "Fetching context for issue #$issue_num..."
    local issue_data=$(gh issue view "$issue_num" --repo "$REPO" --json number,title,state,body,labels,assignees,milestone,createdAt,updatedAt,closedAt,url 2>&1)
    
    if [ $? -ne 0 ]; then
        output_error "Issue #$issue_num not found in repo $REPO"
    fi
    
    # Validate JSON
    if ! echo "$issue_data" | jq . >/dev/null 2>&1; then
        output_error "Issue #$issue_num not found or invalid response from GitHub"
    fi
    
    # Extract basic metadata
    local title=$(echo "$issue_data" | jq -r '.title // empty')
    local state=$(echo "$issue_data" | jq -r '.state // empty')
    local body=$(echo "$issue_data" | jq -r '.body // empty')
    local url=$(echo "$issue_data" | jq -r '.url // empty')
    
    if [ -z "$title" ]; then
        output_error "Failed to extract issue metadata for #$issue_num"
    fi
    
    # Parse acceptance criteria from body (look for ## Acceptance Criteria section)
    local acceptance_criteria=$(echo "$body" | awk '
        BEGIN { in_section = 0; content = "" }
        /^##/ {
            if (in_section) exit
            if ($0 ~ /^## Acceptance Criteria/) in_section = 1
            next
        }
        in_section {
            if (content != "") content = content "\\n"
            content = content $0
        }
        END { print content }
    ')
    
    # Parse tasks/subtasks from body (look for ## Tasks section)
    local tasks_section=$(echo "$body" | awk '
        BEGIN { in_section = 0; content = "" }
        /^##/ {
            if (in_section) exit
            if ($0 ~ /^## (Tasks|Subtasks|Tasks \/ Subtasks)/) in_section = 1
            next
        }
        in_section {
            if (content != "") content = content "\\n"
            content = content $0
        }
        END { print content }
    ')
    
    # Extract linked issues from body (looking for #123 patterns and sub-issue relationships)
    local linked_issues=$(echo "$body" | grep -o '#[0-9]\+' | sed 's/#//' | sort -u | jq -R . | jq -s .)
    
    # Query comments to find "File List" entries
    log_info "Checking comments for file lists..."
    local comments_data=$(gh issue comments "$issue_num" --repo "$REPO" --json body,author 2>&1)
    local file_lists="[]"
    
    if [ $? -eq 0 ] && [ -n "$comments_data" ]; then
        # Look for comments containing "File List" or similar markers
        file_lists=$(echo "$comments_data" | jq '[.[] | select(.body | test("(?i)(file list|files?:)")) | {author: .author.login, content: .body}]')
    fi
    
    # Get sub-issues using GraphQL if available
    log_info "Fetching sub-issues..."
    local node_id=$(gh api "repos/$REPO/issues/$issue_num" --jq '.node_id' 2>/dev/null)
    local sub_issues="[]"
    
    if [ -n "$node_id" ] && [ "$node_id" != "null" ]; then
        local sub_issues_data=$(gh api graphql -f query='
            query($nodeId: ID!) {
                node(id: $nodeId) {
                    ... on Issue {
                        trackedIssues(first: 50) {
                            edges {
                                node {
                                    number
                                    title
                                    state
                                    url
                                }
                            }
                        }
                    }
                }
            }' -f nodeId="$node_id" 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$sub_issues_data" ]; then
            sub_issues=$(echo "$sub_issues_data" | jq '[.data.node.trackedIssues.edges[].node // empty]')
        fi
    fi
    
    # Build comprehensive JSON result
    local result=$(jq -n \
        --arg issue_num "$issue_num" \
        --argjson metadata "$issue_data" \
        --arg acceptance_criteria "$acceptance_criteria" \
        --arg tasks "$tasks_section" \
        --argjson linked_issues "$linked_issues" \
        --argjson file_lists "$file_lists" \
        --argjson sub_issues "$sub_issues" \
        '{
            issue_number: ($issue_num | tonumber),
            metadata: {
                title: $metadata.title,
                state: $metadata.state,
                url: $metadata.url,
                labels: $metadata.labels,
                assignees: $metadata.assignees,
                milestone: $metadata.milestone,
                created_at: $metadata.createdAt,
                updated_at: $metadata.updatedAt,
                closed_at: $metadata.closedAt
            },
            body: $metadata.body,
            parsed_sections: {
                acceptance_criteria: $acceptance_criteria,
                tasks: $tasks
            },
            linked_issues: $linked_issues,
            sub_issues: $sub_issues,
            file_lists: $file_lists
        }')
    
    log_success "Successfully retrieved context for issue #$issue_num"
    output_json "$result"
}

#=============================================================================
# MIGRATION FUNCTIONS
#=============================================================================

migrate_md_to_issues() {
    if [ -z "$REPO" ]; then
        load_config
    fi

    ensure_project_board
    
    # Find story directory using project root
    local story_dir="$PROJECT_ROOT/docs/stories"
    
    if [ ! -d "$story_dir" ]; then
        output_error "Story directory not found at $story_dir"
    fi
    
    # Check if directory has any .md files
    if ! ls "$story_dir"/*.md >/dev/null 2>&1; then
        log_warning "No .md files found in $story_dir"
        output_json "{\"success\": \"Migration completed\", \"epic_count\": 0, \"story_count\": 0, \"message\": \"No files to migrate\"}"
        return 0
    fi
    
    log_info "Starting migration of Markdown stories to GitHub issues..."
    log_info "Story directory: $story_dir"
    
    # Array to track created issues
    declare -A epic_issues
    declare -A story_issues
    
    local migration_log="migration-log-$(date +%Y%m%d-%H%M%S).json"
    echo "{\"migration_started\": \"$(date -Iseconds)\", \"results\": [" > "$migration_log"
    
    local first_result=true
    
    # Function to extract section content from markdown
    extract_section() {
        local file="$1"
        local section="$2"
        
        # Use awk to extract content between ## Section and next ## or end of file
        awk -v section="$section" '
            BEGIN { in_section = 0; content = "" }
            /^##/ {
                if (in_section) exit
                if ($0 ~ "^## " section) in_section = 1
                next
            }
            in_section {
                if (content != "") content = content "\n"
                content = content $0
            }
            END { print content }
        ' "$file"
    }
    
    # Function to parse epic/story numbers from filename
    parse_filename() {
        local filename="$1"
        # Extract pattern like 1.2.story-title.md -> epic=1, story=2
        if [[ $filename =~ ^([0-9]+)\.([0-9]+)\. ]]; then
            local epic_num="${BASH_REMATCH[1]}"
            local story_num="${BASH_REMATCH[2]}"
            echo "$epic_num $story_num"
            return 0
        fi
        return 1
    }
    
    # Function to log result
    log_result() {
        local type="$1"
        local file="$2"
        local issue_num="$3"
        local status="$4"
        local message="$5"
        
        if [ "$first_result" = false ]; then
            echo "," >> "$migration_log"
        fi
        first_result=false
        
        echo "  {" >> "$migration_log"
        echo "    \"type\": \"$type\"," >> "$migration_log"
        echo "    \"file\": \"$file\"," >> "$migration_log"
        echo "    \"issue_number\": $issue_num," >> "$migration_log"
        echo "    \"status\": \"$status\"," >> "$migration_log"
        echo "    \"message\": \"$message\"," >> "$migration_log"
        echo "    \"timestamp\": \"$(date -Iseconds)\"" >> "$migration_log"
        echo -n "  }" >> "$migration_log"
    }
    
    # First pass: Create epic issues if they don't exist
    log_info "Phase 1: Creating epic issues..."
    for story_file in "$story_dir"/*.md; do
        [ -f "$story_file" ] || continue
        
        local filename=$(basename "$story_file")
        local parsed=$(parse_filename "$filename")
        if [ $? -eq 0 ]; then
            local epic_num=$(echo "$parsed" | cut -d' ' -f1)
            if [ -z "${epic_issues[$epic_num]}" ]; then
                log_info "Creating epic issue for Epic $epic_num..."
                
                # Create basic epic issue
                local epic_title="Epic $epic_num: Migration from Markdown"
                local epic_body="This epic was migrated from existing Markdown stories.

Stories in this epic:
$(find "$story_dir" -name "$epic_num.*.md" -exec basename {} \; | sort)"
                
                local epic_slug="epic-$epic_num"
                local result=$(create_epic_issue "$epic_title" "$epic_body" "$epic_slug" 2>&1)
                if echo "$result" | jq -e '.epic_number' >/dev/null 2>&1; then
                    local epic_issue_num=$(echo "$result" | jq -r '.epic_number')
                    epic_issues[$epic_num]=$epic_issue_num
                    log_success "Created epic issue #$epic_issue_num for Epic $epic_num"
                    log_result "epic" "Epic $epic_num" "$epic_issue_num" "created" "Epic migrated successfully"
                else
                    log_error "Failed to create epic issue for Epic $epic_num: $result"
                    log_result "epic" "Epic $epic_num" "null" "failed" "Epic creation failed: $result"
                fi
            fi
        fi
    done
    
    # Second pass: Create story issues
    log_info "Phase 2: Creating story issues..."
    for story_file in "$story_dir"/*.md; do
        [ -f "$story_file" ] || continue
        
        local filename=$(basename "$story_file")
        log_info "Processing story file: $filename"
        
        local parsed=$(parse_filename "$filename")
        if [ $? -eq 0 ]; then
            local epic_num=$(echo "$parsed" | cut -d' ' -f1)
            local story_num=$(echo "$parsed" | cut -d' ' -f2)
            local epic_issue_num=${epic_issues[$epic_num]}
            if [ -z "$epic_issue_num" ]; then
                log_warning "No epic issue found for Epic $epic_num, skipping story"
                log_result "story" "$filename" "null" "skipped" "No parent epic issue found"
                continue
            fi
            
            # Extract story content
            local story_title=$(head -n 1 "$story_file" | sed 's/^# *//')
            if [ -z "$story_title" ]; then
                story_title="Story $epic_num.$story_num"
            fi
            
            # Build story body from markdown sections
            local story_section=$(extract_section "$story_file" "Story")
            local ac_section=$(extract_section "$story_file" "Acceptance Criteria")
            local tasks_section=$(extract_section "$story_file" "Tasks")
            local dev_notes=$(extract_section "$story_file" "Dev Notes")
            
            local story_body="# $story_title

## Story
$story_section

## Acceptance Criteria
$ac_section

## Tasks / Subtasks
$tasks_section

## Dev Notes
$dev_notes

---
*Migrated from: $filename*"
            
            log_info "Creating story issue: $story_title"
            # Generate slugs for migration
            local epic_slug="epic-$epic_num"
            local story_slug="story-$epic_num-$story_num"
            # Use new argument order: title, body, story_slug, epic_num, epic_slug
            local result=$(create_story_issue "$story_title" "$story_body" "$story_slug" "$epic_issue_num" "$epic_slug" 2>&1)
            
            if echo "$result" | jq -e '.story_number' >/dev/null 2>&1; then
                local story_issue_num=$(echo "$result" | jq -r '.story_number')
                story_issues["$epic_num.$story_num"]=$story_issue_num
                log_success "Created story issue #$story_issue_num for $filename"
                log_result "story" "$filename" "$story_issue_num" "created" "Story migrated successfully"
                
                # Add migration label
                gh issue edit "$story_issue_num" --add-label "migrated" --repo "$REPO" >/dev/null 2>&1
                
            else
                log_error "Failed to create story issue for $filename: $result"
                log_result "story" "$filename" "null" "failed" "Story creation failed: $result"
            fi
        else
            log_warning "Could not parse filename format: $filename"
            log_result "story" "$filename" "null" "skipped" "Filename format not recognized"
        fi
    done
    
    # Close migration log
    echo "" >> "$migration_log"
    echo "], \"migration_completed\": \"$(date -Iseconds)\"}" >> "$migration_log"
    
    log_success "Migration completed!"
    
    # Get accurate counts using array length
    local epic_count=${#epic_issues[@]}
    local story_count=${#story_issues[@]}
    
    log_info "Created $epic_count epic issues"
    log_info "Created $story_count story issues"
    log_info "Migration log saved to: $migration_log"
    
    output_json "{\"success\": \"Migration completed\", \"epic_count\": $epic_count, \"story_count\": $story_count, \"log_file\": \"$migration_log\", \"story_dir\": \"$story_dir\"}"
}

#=============================================================================
# ARGUMENT PARSING HELPERS
#=============================================================================

# Parse create-story arguments
# Syntax: create-story <title> <body> <story_slug> [--epic <epic_num> <epic_slug>]
parse_create_story_args() {
    local title=""
    local body=""
    local story_slug=""
    local epic_num=""
    local epic_slug=""
    
    if [ $# -lt 3 ]; then
        output_error "Usage: create-story <title> <body> <story_slug> [--epic <epic_num> <epic_slug>]"
    fi
    
    title="$1"
    body="$2"
    story_slug="$3"
    shift 3
    
    # Parse optional flags
    while [ $# -gt 0 ]; do
        case "$1" in
            --epic)
                if [ $# -lt 3 ]; then
                    output_error "--epic requires two arguments: <epic_num> <epic_slug>"
                fi
                epic_num="$2"
                epic_slug="$3"
                shift 3
                ;;
            *)
                output_error "Unknown option: $1"
                ;;
        esac
    done
    
    # Call create_story_issue with parameter order: title, body, story_slug, epic_num, epic_slug
    create_story_issue "$title" "$body" "$story_slug" "$epic_num" "$epic_slug"
}

# Parse create-task arguments
# Syntax: create-task <title> <body> [--story <story_num> <story_slug>] [--epic-slug <epic_slug>]
parse_create_task_args() {
    local title=""
    local body=""
    local story_num=""
    local story_slug=""
    local epic_slug=""
    
    if [ $# -lt 2 ]; then
        output_error "Usage: create-task <title> <body> [--story <story_num> <story_slug>] [--epic-slug <epic_slug>]"
    fi
    
    title="$1"
    body="$2"
    shift 2
    
    # Parse optional flags
    while [ $# -gt 0 ]; do
        case "$1" in
            --story)
                if [ $# -lt 3 ]; then
                    output_error "--story requires two arguments: <story_num> <story_slug>"
                fi
                story_num="$2"
                story_slug="$3"
                shift 3
                ;;
            --epic-slug)
                if [ $# -lt 2 ]; then
                    output_error "--epic-slug requires one argument: <epic_slug>"
                fi
                epic_slug="$2"
                shift 2
                ;;
            *)
                output_error "Unknown option: $1"
                ;;
        esac
    done
    
    # Call create_task_issue with parameter order: title, body, story_num, story_slug, epic_slug
    create_task_issue "$title" "$body" "$story_num" "$story_slug" "$epic_slug"
}

# Parse create-sub-epic arguments
# Syntax: create-sub-epic <title> <body> <sub_epic_slug> --parent <parent_epic_num> <parent_epic_slug>
parse_create_sub_epic_args() {
    local title=""
    local body=""
    local sub_epic_slug=""
    local parent_epic_num=""
    local parent_epic_slug=""
    
    if [ $# -lt 3 ]; then
        output_error "Usage: create-sub-epic <title> <body> <sub_epic_slug> --parent <parent_epic_num> <parent_epic_slug>"
    fi
    
    title="$1"
    body="$2"
    sub_epic_slug="$3"
    shift 3
    
    # Parse required --parent flag
    while [ $# -gt 0 ]; do
        case "$1" in
            --parent)
                if [ $# -lt 3 ]; then
                    output_error "--parent requires two arguments: <parent_epic_num> <parent_epic_slug>"
                fi
                parent_epic_num="$2"
                parent_epic_slug="$3"
                shift 3
                ;;
            *)
                output_error "Unknown option: $1"
                ;;
        esac
    done
    
    # Call create_sub_epic_issue with parameter order: title, body, sub_epic_slug, parent_epic_num, parent_epic_slug
    create_sub_epic_issue "$title" "$body" "$sub_epic_slug" "$parent_epic_num" "$parent_epic_slug"
}

#=============================================================================
# MAIN COMMAND HANDLER
#=============================================================================

main() {
    if [ $# -eq 0 ]; then
        print_usage
        exit 1
    fi
    
    local command="$1"
    shift
    
    case "$command" in
        "create-epic")
            if [ $# -lt 3 ]; then
                output_error "Usage: create-epic <title> <body> <epic_slug>"
            fi
            create_epic_issue "$1" "$2" "$3"
            ;;
        "create-sub-epic")
            parse_create_sub_epic_args "$@"
            ;;
        "create-story")
            parse_create_story_args "$@"
            ;;
        "create-task")
            parse_create_task_args "$@"
            ;;
        "update-status")
            if [ $# -lt 2 ]; then
                output_error "Usage: update-status <issue_num> <status>"
            fi
            update_issue_status "$1" "$2"
            ;;
        "list-stories")
            list_stories "$1"
            ;;
        "migrate-stories")
            migrate_md_to_issues
            ;;
        "get-story-context")
            if [ $# -lt 1 ]; then
                output_error "Usage: get-story-context <issue_num>"
            fi
            get_story_context "$1"
            ;;
        "help"|"-h"|"--help")
            print_usage
            ;;
        "version"|"-v"|"--version")
            print_version
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            print_usage
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"