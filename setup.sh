#!/bin/bash

# Make scripts executable in their repository location
chmod +x /workspace/easy/easy.sh
chmod +x /workspace/easy/fix-aliases.sh

# Install dependencies
pip install -r requirements.txt

# Run our alias fix script instead of using easy_alias.py
/workspace/easy/fix-aliases.sh

# Set up rclone configuration if needed
mkdir -p ~/.config/rclone
if [ -f /workspace/rclone.conf ]; then
  cp /workspace/rclone.conf ~/.config/rclone/
  echo "Rclone configuration set up successfully"
else
  echo "Warning: /workspace/rclone.conf not found. Rclone setup skipped."
fi

echo "Setup complete! After sourcing your config, you can use the 'easy' command."
echo "Use 'source ~/.bashrc' to activate the alias immediately."
echo "Note: This setup no longer manages comfy-download. To set it up, run:"
echo "cd /workspace/comfy-download && bash setup.sh"
