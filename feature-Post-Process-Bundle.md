# Feature: Post-Process Bundle

## Current Feature Branch
```
feature/post-process
```

## Todo Checklist
- [ ] Update lora_mover.py with standardized two-step UI
- [ ] Update lora_sync.py with standardized two-step UI
- [ ] Create download_output.py with standardized two-step UI
- [ ] Update easy.py to include the new download_output command
- [ ] Test all implementations with real config data
- [ ] Document the new functionality

## Implementation Details

### Standardized Two-Step UI
All tools will follow the standardized UI pattern as defined in the knowledge checkpoint:
- First step: Select config family (prefix)
- Second step: Select specific config or "all"

### download_output.py
This new script will:
1. Allow users to select a configuration using the two-step UI
2. Filter output content:
   - Keep only the highest checkpoint folder
   - Exclude validation_images folder
   - Exclude pytorch_lora_weights.safetensors files
3. Upload filtered content to Dropbox with proper path structure:
   - Destination: /studio/ai/data/1models/013-{Family}/4training/output/{config_name}

## Progress Tracking
- Started implementation: March 23, 2025
