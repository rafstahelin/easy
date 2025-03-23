<<<<<<< Updated upstream
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
=======
# Post-Process Bundle Implementation Plan

## Current Feature Branch
feature/post-process

## Overview

This document outlines the strategy for implementing a bundled post-processing workflow (`easy pp`) that allows users to select a configuration once and apply multiple tools sequentially against that selection. The implementation will combine five existing tools:

1. LoRA Mover
2. Validation Grid
3. Dataset Grid
4. Download Config
5. Download Output (new tool to be developed)

## Current Development Progress

### Immediate Tasks (Current Sprint)
- [x] Create feature branch and planning document
- [ ] Update lora_mover.py with standardized two-step UI
- [ ] Update lora_sync.py with standardized two-step UI
- [ ] Create download_output.py with standardized two-step UI
- [ ] Update easy.py to include the new download_output command
- [ ] Test implementations with real configuration data
- [ ] Commit changes to feature branch

### Implementation Details for Current Tasks

#### Standardized Two-Step UI
All tools will follow the standardized UI pattern:
- First step: Select config family (prefix)
- Second step: Select specific config or "all"

#### download_output.py
This new script will:
1. Allow users to select a configuration using the two-step UI
2. Filter output content:
   - Keep only the highest checkpoint folder
   - Exclude validation_images folder
   - Exclude pytorch_lora_weights.safetensors files
3. Upload filtered content to Dropbox with proper path structure:
   - Destination: /studio/ai/data/1models/013-{Family}/4training/output/{config_name}

## Original Development Plan

### Development Phases

### Phase 1: Shared Configuration Selector

Create a reusable module that handles the two-step configuration selection process:

- Extract the common selection UI logic from existing tools
- Define standard input/output interfaces
- Implement with standalone testing capabilities

**Tasks:**
- [ ] Create `classes/config_selector.py` module
- [ ] Implement two-step selection UI (family → specific config)
- [ ] Add option for "all" configurations in a family
- [ ] Ensure consistent styling with existing tools
- [ ] Add basic documentation
- [ ] Test standalone functionality

### Phase 2: Tool Refactoring

Modify each tool to support both standalone and pre-selected configuration modes:

**Tasks:**
- [ ] Refactor `classes/dataset_grid.py`:
  - [ ] Add `run_with_config(config)` method
  - [ ] Update `run()` to use the shared selector
  - [ ] Test both modes

- [ ] Refactor `classes/validation_grid.py`:
  - [ ] Add `run_with_config(config)` method
  - [ ] Update `run()` to use the shared selector
  - [ ] Test both modes

- [ ] Refactor `classes/download_configs.py`:
  - [ ] Add `run_with_config(config)` method
  - [ ] Update `run()` to use the shared selector
  - [ ] Test both modes

### Phase 3: LoRA Mover Update

Bring the LoRA Mover tool in line with the consistent selection pattern:

**Tasks:**
- [ ] Update `classes/lora_mover.py`:
  - [ ] Implement the two-step selection UI
  - [ ] Add `run_with_config(config)` method
  - [ ] Ensure consistent styling
  - [ ] Test both modes

### Phase 4: Download Output Tool Development

Create a new tool for downloading the output of training:

**Tasks:**
- [ ] Create `classes/download_output.py` module
  - [ ] Implement two-step selection UI using shared selector
  - [ ] Add logic to locate config's output path (/workspace/SimpleTuner/output/{config_name})
  - [ ] Add filtering to download only the latest model (pytorch.safetensor) from training steps
  - [ ] Implement download functionality for all other output content
  - [ ] Add progress indicators
  - [ ] Add error handling
  - [ ] Test as standalone tool

### Phase 5: Bundle Orchestrator

Create the post-process orchestrator that ties everything together:

**Tasks:**
- [ ] Create `classes/post_process.py` orchestrator
  - [ ] Implement main workflow with ConfigSelector
  - [ ] Add sequential tool execution for all five tools
  - [ ] Implement error handling (continue on individual tool errors)
  - [ ] Add progress indicators
  - [ ] Test the complete workflow

- [ ] Update `easy.py` to include the new `pp` command
  - [ ] Add command-line arguments for post-process
  - [ ] Add help documentation

### Phase 6: Testing & Integration

Comprehensive testing of the full implementation:

**Tasks:**
- [ ] Test individual tools in standalone mode
- [ ] Test the complete bundle workflow
- [ ] Test error scenarios and recovery
- [ ] Verify backward compatibility
- [ ] Address any integration issues

## Implementation Checklist

### Configuration Selector
- [ ] Extract common selection logic
- [ ] Implement family prefix detection
- [ ] Implement two-column display UI
- [ ] Handle "all" option correctly
- [ ] Add proper error handling
- [ ] Document public methods

### Tool Refactoring
- [ ] Add dual-mode support to all tools
- [ ] Ensure consistent styling across tools
- [ ] Maintain backward compatibility
- [ ] Ensure proper error handling
- [ ] Update function documentation

### LoRA Mover Alignment
- [ ] Update selection UI to match other tools
- [ ] Preserve existing functionality
- [ ] Handle edge cases specific to LoRA Mover
- [ ] Test thoroughly

### Download Output Tool
- [ ] Implement family/config selection UI
- [ ] Add output path detection logic
- [ ] Implement selective model downloading (only latest)
- [ ] Implement full content downloading (except early models)
- [ ] Add proper error handling
- [ ] Test with various configuration types

### Bundle Orchestrator
- [ ] Implement sequential workflow for all five tools
- [ ] Add clear progress indicators
- [ ] Provide summary of results
- [ ] Handle tool-specific errors
- [ ] Add command-line integration
>>>>>>> Stashed changes

## Progress Tracking
- Started implementation: March 23, 2025