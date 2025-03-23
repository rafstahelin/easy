#!/bin/bash

# This script ensures all easy repository aliases are properly set up
# without conflicting with other repositories

# First, remove any existing easy-specific aliases
sed -i '/alias easy=/d' ~/.bashrc

# Now add the alias to .bashrc with clear comment markers
if ! grep -q '# BEGIN EASY ALIASES' ~/.bashrc; then
  cat >> ~/.bashrc << 'EOF'

# BEGIN EASY ALIASES
# These aliases are managed by the easy repository
alias easy="/workspace/easy/easy.sh"
# END EASY ALIASES
EOF
fi

echo "Easy repository aliases have been updated."
echo "Run 'source ~/.bashrc' to activate them in this session."
