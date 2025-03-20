#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Set up easy alias using the Python script
python easy_alias.py easy /workspace/easy/easy.sh

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
echo "To set up comfy-download, please run: cd /workspace/comfy-download && bash setup.sh"
