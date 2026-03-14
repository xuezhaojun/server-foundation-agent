#!/usr/bin/env bash

# Standalone script to fetch all PRs from a specific GitHub Project Board with detailed information
# This script uses optimized GraphQL queries to minimize API calls and caches results locally
#
# Fixed Configuration:
#   Organization: stolostron
#   Project Number: 8
#
# Usage:
#   ./fetch-project-prs.sh [detail_level] [nocache]
#   Or source this file and call fetch_project_prs function directly
#
# Environment Variables:
#   CACHE_DIR  - Cache directory path (default: .cache)
#   CACHE_TTL  - Cache time-to-live in seconds (default: 300)
#
# Example:
#   ./fetch-project-prs.sh
#   ./fetch-project-prs.sh detailed
#   ./fetch-project-prs.sh detailed nocache
#   CACHE_TTL=120 ./fetch-project-prs.sh all
#   Output: JSON array of all PRs with their details

# Exit on undefined variables
set -u

# Fixed project configuration
readonly FIXED_ORG="stolostron"
readonly FIXED_PROJECT_NUMBER=8

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Cache configuration
CACHE_DIR="${CACHE_DIR:-${TMPDIR:-/tmp}/sf-claude-code-plugins-fetch-prs-${USER}}"
CACHE_TTL="${CACHE_TTL:-300}" # Default 5 minutes (300 seconds)

# Function to log messages to stderr (so stdout remains clean for JSON output)
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check GitHub API rate limit
# Parameters:
#   $1 - (optional) "strict" to exit immediately if rate limit is 0
check_rate_limit() {
    local strict_mode=${1:-""}
    log_info "Checking GitHub API rate limit..."
    local rate_limit_info=$(gh api rate_limit 2>/dev/null)

    if [ -z "$rate_limit_info" ]; then
        log_warn "Could not fetch rate limit information"
        return 0
    fi

    # Check both REST and GraphQL rate limits
    local core_remaining=$(echo "$rate_limit_info" | jq -r '.resources.core.remaining')
    local core_limit=$(echo "$rate_limit_info" | jq -r '.resources.core.limit')
    local core_reset=$(echo "$rate_limit_info" | jq -r '.resources.core.reset')

    local graphql_remaining=$(echo "$rate_limit_info" | jq -r '.resources.graphql.remaining')
    local graphql_limit=$(echo "$rate_limit_info" | jq -r '.resources.graphql.limit')
    local graphql_reset=$(echo "$rate_limit_info" | jq -r '.resources.graphql.reset')

    log_info "API Rate Limit - REST: $core_remaining/$core_limit, GraphQL: $graphql_remaining/$graphql_limit"

    # In strict mode, exit immediately if rate limit is 0
    if [ "$strict_mode" = "strict" ]; then
        if [ "$graphql_remaining" -eq 0 ] || [ "$core_remaining" -eq 0 ]; then
            local current_time=$(date +%s)

            if [ "$graphql_remaining" -eq 0 ]; then
                local wait_time=$((graphql_reset - current_time))
                local reset_date=$(date -r "$graphql_reset" 2>/dev/null || date -d "@$graphql_reset" 2>/dev/null || echo "unknown")
                log_error "GraphQL API rate limit exhausted: 0/$graphql_limit remaining"
                log_error "Rate limit will reset at: $reset_date (in $((wait_time / 60)) minutes, $wait_time seconds)"
            fi

            if [ "$core_remaining" -eq 0 ]; then
                local wait_time=$((core_reset - current_time))
                local reset_date=$(date -r "$core_reset" 2>/dev/null || date -d "@$core_reset" 2>/dev/null || echo "unknown")
                log_error "REST API rate limit exhausted: 0/$core_limit remaining"
                log_error "Rate limit will reset at: $reset_date (in $((wait_time / 60)) minutes, $wait_time seconds)"
            fi

            log_error "Aborting script execution. Please wait for rate limit to reset and try again."
            return 2  # Return 2 to indicate rate limit exhausted
        fi
    fi

    # Warn if GraphQL rate limit is too low
    if [ "$graphql_remaining" -lt 100 ]; then
        local reset_date=$(date -r "$graphql_reset" 2>/dev/null || date -d "@$graphql_reset" 2>/dev/null || echo "unknown")
        log_error "GraphQL API rate limit is too low: $graphql_remaining requests remaining"
        log_error "Rate limit will reset at: $reset_date"

        # In strict mode, don't continue even if > 0 but < 100
        if [ "$strict_mode" = "strict" ]; then
            log_error "Rate limit too low for safe operation. Please wait for reset."
            return 2
        fi

        log_error "Please wait until the rate limit resets before running this script again"
        return 1
    fi

    # Warn if REST API rate limit is too low
    if [ "$core_remaining" -lt 100 ]; then
        local reset_date=$(date -r "$core_reset" 2>/dev/null || date -d "@$core_reset" 2>/dev/null || echo "unknown")
        log_warn "REST API rate limit is low: $core_remaining requests remaining"
        log_warn "Rate limit will reset at: $reset_date"

        # In strict mode, don't continue
        if [ "$strict_mode" = "strict" ]; then
            log_error "Rate limit too low for safe operation. Please wait for reset."
            return 2
        fi
    fi

    return 0
}

# Get cache file path for a given organization and project
# Args:
#   $1 - Organization name
#   $2 - Project number
#   $3 - Detail level
# Returns:
#   Cache file path
get_cache_file() {
    local org=$1
    local project_number=$2
    local detail_level=$3
    echo "$CACHE_DIR/prs_${org}_${project_number}_${detail_level}.json"
}

# Check if cache is valid
# Args:
#   $1 - Cache file path
# Returns:
#   0 if cache is valid, 1 otherwise
is_cache_valid() {
    local cache_file=$1

    if [ ! -f "$cache_file" ]; then
        return 1
    fi

    local current_time=$(date +%s)
    local file_mtime=$(stat -f %m "$cache_file" 2>/dev/null || stat -c %Y "$cache_file" 2>/dev/null)

    if [ -z "$file_mtime" ]; then
        return 1
    fi

    local age=$((current_time - file_mtime))

    if [ $age -lt $CACHE_TTL ]; then
        log_info "Cache is valid (age: ${age}s, TTL: ${CACHE_TTL}s)"
        return 0
    else
        log_info "Cache expired (age: ${age}s, TTL: ${CACHE_TTL}s)"
        return 1
    fi
}

# Save data to cache
# Args:
#   $1 - Cache file path
#   $2 - JSON data to cache
save_to_cache() {
    local cache_file=$1
    local data=$2

    # Create cache directory if it doesn't exist
    mkdir -p "$CACHE_DIR"

    echo "$data" > "$cache_file"
    log_info "Saved to cache: $cache_file"
}

# Load data from cache
# Args:
#   $1 - Cache file path
# Returns:
#   Cached JSON data
load_from_cache() {
    local cache_file=$1
    cat "$cache_file"
    log_info "Loaded from cache: $cache_file"
}

# Fetch all project items with PR states using GraphQL (paginated)
# This function retrieves project items along with their PR states in a single API call per page,
# significantly reducing the total number of API calls compared to fetching states individually.
#
# Args:
#   $1 - Organization name (e.g., "stolostron")
#   $2 - Project number (e.g., 8)
#   $3 - (optional) Fields to include: "basic" (default), "detailed", or "all"
#   $4 - (optional) Skip cache: "nocache" to bypass cache, otherwise use cache
#
# Returns:
#   JSON array of all project items with their PR states to stdout
fetch_project_prs() {
    local org=$1
    local project_number=$2
    local detail_level=${3:-"basic"}
    local skip_cache=${4:-""}
    local cache_file=$(get_cache_file "$org" "$project_number" "$detail_level")

    # Check cache first (unless nocache flag is set)
    if [ "$skip_cache" != "nocache" ] && is_cache_valid "$cache_file"; then
        load_from_cache "$cache_file"
        return 0
    fi

    local all_items="[]"
    local cursor=""
    local has_next_page=true
    local page_count=0

    log_info "Fetching project PRs from $org/project/$project_number via GraphQL..."

    # Build GraphQL query based on detail level
    local pr_fields
    case "$detail_level" in
        basic)
            pr_fields='url
                          number
                          state
                          repository {
                            nameWithOwner
                          }'
            ;;
        detailed)
            pr_fields='url
                          number
                          title
                          state
                          createdAt
                          updatedAt
                          author {
                            login
                          }
                          repository {
                            nameWithOwner
                          }
                          labels(first: 10) {
                            nodes {
                              name
                            }
                          }'
            ;;
        all)
            pr_fields='url
                          number
                          title
                          state
                          createdAt
                          updatedAt
                          mergedAt
                          closedAt
                          author {
                            login
                          }
                          assignees(first: 10) {
                            nodes {
                              login
                            }
                          }
                          repository {
                            nameWithOwner
                          }
                          labels(first: 10) {
                            nodes {
                              name
                            }
                          }
                          reviewDecision
                          isDraft
                          mergeable'
            ;;
        *)
            log_error "Invalid detail level: $detail_level (use: basic, detailed, or all)"
            return 1
            ;;
    esac

    while [ "$has_next_page" = "true" ]; do
        ((page_count++))
        log_info "Fetching page $page_count..."

        # Build the GraphQL query dynamically
        local response
        if [ -z "$cursor" ]; then
            # First page: no cursor
            response=$(gh api graphql -f query="{
              organization(login: \"$org\") {
                projectV2(number: $project_number) {
                  items(first: 100) {
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                    nodes {
                      id
                      content {
                        ... on PullRequest {
                          $pr_fields
                        }
                        ... on Issue {
                          url
                        }
                      }
                    }
                  }
                }
              }
            }")
        else
            # Subsequent pages: with cursor
            response=$(gh api graphql -f query="{
              organization(login: \"$org\") {
                projectV2(number: $project_number) {
                  items(first: 100, after: \"$cursor\") {
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                    nodes {
                      id
                      content {
                        ... on PullRequest {
                          $pr_fields
                        }
                        ... on Issue {
                          url
                        }
                      }
                    }
                  }
                }
              }
            }")
        fi

        if [ -z "$response" ]; then
            log_error "Failed to fetch project items via GraphQL (empty response)"
            return 1
        fi

        # Check for GraphQL errors
        if echo "$response" | jq -e '.errors' > /dev/null 2>&1; then
            log_error "GraphQL query returned errors: $(echo "$response" | jq -r '.errors[0].message')"
            return 1
        fi

        # Extract items and append
        local page_items=$(echo "$response" | jq -c '.data.organization.projectV2.items.nodes')
        all_items=$(echo "$all_items" "$page_items" | jq -s 'add')

        # Update pagination
        has_next_page=$(echo "$response" | jq -r '.data.organization.projectV2.items.pageInfo.hasNextPage')
        cursor=$(echo "$response" | jq -r '.data.organization.projectV2.items.pageInfo.endCursor')

        if [ "$cursor" = "null" ] || [ -z "$cursor" ]; then
            break
        fi
    done

    # Filter to only PRs (exclude issues and null content)
    local prs_only=$(echo "$all_items" | jq '[.[] | select(.content.number != null and .content.repository != null)]')
    local pr_count=$(echo "$prs_only" | jq 'length')

    log_info "Fetched $pr_count PRs in $page_count page(s)"

    # Save to cache
    save_to_cache "$cache_file" "$prs_only"

    # Output JSON to stdout
    echo "$prs_only"
}

# Get PR statistics from fetched data
# Args:
#   $1 - JSON array of PRs (from fetch_project_prs)
#
# Returns:
#   JSON object with statistics
get_pr_statistics() {
    local prs=$1

    local total=$(echo "$prs" | jq 'length')
    local open=$(echo "$prs" | jq '[.[] | select(.content.state == "OPEN")] | length')
    local merged=$(echo "$prs" | jq '[.[] | select(.content.state == "MERGED")] | length')
    local closed=$(echo "$prs" | jq '[.[] | select(.content.state == "CLOSED")] | length')

    # Group by repository
    local by_repo=$(echo "$prs" | jq -r 'group_by(.content.repository.nameWithOwner) | map({repo: .[0].content.repository.nameWithOwner, count: length}) | sort_by(.count) | reverse')

    # Create statistics JSON
    jq -n \
        --arg total "$total" \
        --arg open "$open" \
        --arg merged "$merged" \
        --arg closed "$closed" \
        --argjson by_repo "$by_repo" \
        '{
            total: ($total | tonumber),
            by_state: {
                open: ($open | tonumber),
                merged: ($merged | tonumber),
                closed: ($closed | tonumber)
            },
            by_repository: $by_repo
        }'
}

# Filter PRs by state
# Args:
#   $1 - JSON array of PRs
#   $2 - State to filter by (OPEN, MERGED, CLOSED)
filter_prs_by_state() {
    local prs=$1
    local state=$2

    echo "$prs" | jq --arg state "$state" '[.[] | select(.content.state == $state)]'
}

# Filter PRs by repository
# Args:
#   $1 - JSON array of PRs
#   $2 - Repository name (e.g., "stolostron/ocm")
filter_prs_by_repo() {
    local prs=$1
    local repo=$2

    echo "$prs" | jq --arg repo "$repo" '[.[] | select(.content.repository.nameWithOwner == $repo)]'
}

# Export functions for sourcing
export -f fetch_project_prs
export -f get_pr_statistics
export -f filter_prs_by_state
export -f filter_prs_by_repo
export -f get_cache_file
export -f is_cache_valid
export -f save_to_cache
export -f load_from_cache
export -f log_info
export -f log_warn
export -f log_error

# Main execution (only when run as script, not sourced)
main() {
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    log_info "Starting fetch-prs script..."

    # Check API rate limit BEFORE starting (strict mode - exit if rate limit = 0 or < 100)
    log_info "Checking API rate limits before starting..."
    if ! check_rate_limit "strict"; then
        log_error "Cannot proceed due to insufficient API rate limit"
        exit 1
    fi

    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        log_error "gh CLI is not installed. Please install it first: https://cli.github.com/"
        exit 1
    fi

    # Check if authenticated with gh
    if ! gh auth status &> /dev/null; then
        log_error "Not authenticated with GitHub CLI. Please run: gh auth login"
        exit 1
    fi

    # Check for required scopes
    log_info "Checking GitHub authentication scopes..."
    if ! gh project list --owner "$(gh api user --jq '.login')" --limit 1 &> /dev/null; then
        log_error "Missing required GitHub scopes for project access."
        log_error "Please run: gh auth refresh -s project"
        exit 1
    fi

    # Parse arguments
    DETAIL_LEVEL=${1:-"basic"}
    SKIP_CACHE=${2:-""}

    # Validate detail level
    if [ "$DETAIL_LEVEL" != "basic" ] && [ "$DETAIL_LEVEL" != "detailed" ] && [ "$DETAIL_LEVEL" != "all" ] && [ "$DETAIL_LEVEL" != "nocache" ]; then
        echo "Usage: $0 [detail_level] [nocache]" >&2
        echo "" >&2
        echo "Fixed Configuration:" >&2
        echo "  Organization:   $FIXED_ORG" >&2
        echo "  Project Number: $FIXED_PROJECT_NUMBER" >&2
        echo "" >&2
        echo "Arguments:" >&2
        echo "  detail_level   - Optional: basic (default), detailed, or all" >&2
        echo "  nocache        - Optional: skip cache and force fresh fetch" >&2
        echo "" >&2
        echo "Environment Variables:" >&2
        echo "  CACHE_DIR      - Cache directory (default: .cache)" >&2
        echo "  CACHE_TTL      - Cache TTL in seconds (default: 300)" >&2
        echo "" >&2
        echo "Examples:" >&2
        echo "  $0" >&2
        echo "  $0 detailed" >&2
        echo "  $0 detailed nocache" >&2
        echo "  CACHE_TTL=120 $0 all > prs.json" >&2
        exit 1
    fi

    # Handle case where first arg is "nocache"
    if [ "$DETAIL_LEVEL" = "nocache" ]; then
        DETAIL_LEVEL="basic"
        SKIP_CACHE="nocache"
    fi

    # Fetch and output PRs using fixed configuration
    fetch_project_prs "$FIXED_ORG" "$FIXED_PROJECT_NUMBER" "$DETAIL_LEVEL" "$SKIP_CACHE"
fi
}

main "$@"