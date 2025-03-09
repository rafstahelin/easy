#!/bin/bash
# Install dependencies
pip install -r requirements.txt

# Set up easy alias using the Python script
python easy_alias.py easy /workspace/easy/easy.sh

# Create the dl-manager.sh script in comfy-download directory
cat > /workspace/comfy-download/dl-manager.sh << 'EOF'
#!/bin/bash

command="$1"

case "$command" in
  start)
    service cron start
    (crontab -l 2>/dev/null | grep -q 'comfy-download' || (crontab -l 2>/dev/null; echo '* * * * * /workspace/comfy-download/download_run.sh') | crontab -)
    echo 'Image download system started!'
    ;;
  
  stop)
    (crontab -l 2>/dev/null | grep -v 'comfy-download' | crontab -)
    echo 'Image download system stopped!'
    ;;
  
  status)
    TODAY=$(date +%Y-%m-%d)
    echo "Today: $TODAY"
    echo "Log entries: $(cat /workspace/ComfyUI/logs/downloaded_$TODAY.log 2>/dev/null | wc -l)"
    echo "Unique files downloaded: $(sort /workspace/ComfyUI/logs/downloaded_$TODAY.log 2>/dev/null | uniq | wc -l)"
    echo "Files in output folder: $(find /workspace/ComfyUI/output/$TODAY -type f -name "*.png" 2>/dev/null | wc -l)"
    ;;
  
  run)
    /workspace/comfy-download/download_images.sh
    ;;
  
  reset)
    TODAY=$(date +%Y-%m-%d)
    echo "Backing up old log to downloaded_$TODAY.bak"
    cp /workspace/ComfyUI/logs/downloaded_$TODAY.log /workspace/ComfyUI/logs/downloaded_$TODAY.log.bak 2>/dev/null || true
    echo "Cleaning log file"
    cat /workspace/ComfyUI/logs/downloaded_$TODAY.log.bak 2>/dev/null | sort | uniq > /workspace/ComfyUI/logs/downloaded_$TODAY.log 2>/dev/null || true
    echo "Done."
    ;;
  
  help|*)
    echo "Download Manager Command Reference:"
    echo "----------------------------------"
    echo "dl start   - Start the automatic download system"
    echo "dl stop    - Stop the automatic download system"
    echo "dl status  - Show current download statistics"
    echo "dl run     - Run a download check manually once"
    echo "dl reset   - Clean up duplicate entries in the log file"
    echo "dl help    - Display this help message"
    ;;
esac
EOF

# Make the dl-manager script executable
chmod +x /workspace/comfy-download/dl-manager.sh

# Create necessary directories
mkdir -p /workspace/ComfyUI/logs

# Make other scripts executable
chmod +x /workspace/comfy-download/download_images.sh
chmod +x /workspace/comfy-download/download_run.sh

# Add the dl alias to bashrc if it doesn't already exist
if ! grep -q 'alias dl=' ~/.bashrc; then
  echo 'alias dl="/workspace/comfy-download/dl-manager.sh"' >> ~/.bashrc
  echo "Added dl alias to ~/.bashrc"
fi

echo "Setup complete! After sourcing your config, you can use your aliases."
echo "Use 'source ~/.bashrc' to activate the aliases immediately."
echo "Use 'easy' to run the easy script"
echo "Use 'dl help' to see download manager commands"