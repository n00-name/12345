#!/bin/bash

# Change to the root directory of the Git repository
cd "$(git rev-parse --show-toplevel)"

# Copy all files in the hooks directory to the .git/hooks directory
for hook in hooks/*; do
  cp "$hook" .git/hooks/
  chmod +x ".git/hooks/$(basename "$hook")"
done
