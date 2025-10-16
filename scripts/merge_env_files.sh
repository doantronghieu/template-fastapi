#!/bin/bash
# Merge all .env* files for Docker containers
# This ensures extensions' environment variables are available in containers

set -e

# Output file
OUTPUT_FILE=".env.docker"

# Start fresh
rm -f "$OUTPUT_FILE"

echo "# Auto-generated merged environment file for Docker containers" > "$OUTPUT_FILE"
echo "# Generated at: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Find and merge all .env* files (excluding backups, examples, and docker file itself)
for env_file in .env .env.*; do
    # Skip if file doesn't exist (glob didn't match)
    [ -f "$env_file" ] || continue

    # Skip backup files, example files, and the output file itself
    [[ "$env_file" == *.bak ]] && continue
    [[ "$env_file" == *.backup ]] && continue
    [[ "$env_file" == *.example ]] && continue
    [[ "$env_file" == "$OUTPUT_FILE" ]] && continue

    echo "Merging: $env_file"
    echo "" >> "$OUTPUT_FILE"
    echo "# From: $env_file" >> "$OUTPUT_FILE"
    cat "$env_file" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
done

echo "✓ Environment files merged into $OUTPUT_FILE"
