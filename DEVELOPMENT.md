# Easy CLI - Development Guide

## Environment Overview

The Easy CLI is designed to run in a RunPod environment with the following characteristics:

- **RunPod Instance**: Persistent storage GPU instance optimized for ML workloads
- **Environment**: Linux-based container with CUDA support
- **Development Interfaces**: SSH terminal, Jupyter Notebook, VSCode Server
- **Storage**: Network volume mounted to `/workspace` for persistence between sessions
- **GPU Access**: Direct access to NVIDIA GPUs for accelerated training and inference

## Project Architecture

The Easy CLI is part of a larger ML workflow pipeline:

```
┌─────────────────┐                 ┌─────────────────┐
│ ML Training     │                 │ Inference & UI  │
│ ----------      │                 │ -----------     │
│ SimpleTuner     │────────────────▶│ ComfyUI         │
│ Easy (CLI)      │                 │ comfy-download  │
└─────────────────┘                 └─────────────────┘
```

### Related Projects

- `/workspace/easy/`: CLI wrapper for SimpleTuner training orchestration (this repository)
- `/workspace/SimpleTuner/`: Core ML training framework (underlying engine)
- `/workspace/ComfyUI/`: Visual interface for model inference and testing
- `/workspace/comfy-download/`: ComfyUI workflow management and synchronization utilities

## Development Workflow

### Setup

1. Connect to RunPod instance through your assigned URL
2. Use provided credentials for authentication
3. Select your preferred interface (Terminal, Jupyter, VSCode)
4. Default working directory is `/workspace`

### Common Development Tasks

- Modify CLI command handlers in `easy.py`
- Extend functionality in `classes/` modules
- Update prompt templates in `prompts/` directory
- Test changes with `./easy.py [command] [options]`

### Git Workflow

1. Create feature branches for development:
   ```bash
   git checkout -b feature/descriptive-name
   ```
2. Make focused, incremental changes
3. Commit changes with descriptive messages
4. Push changes to GitHub for review
5. Create pull requests for code review

### Testing

- Create test training configurations with small step counts
- Validate configuration generation works correctly
- Test model movement to ComfyUI locations
- Verify grid generation with test checkpoints

## Repository Structure

```
/workspace/easy/
├── classes/               # Core tool implementations
│   ├── download_configs.py
│   ├── validation_grid.py
│   ├── dataset_grid.py
│   ├── lora_mover.py
│   └── lora_sync.py
├── easy.py                # Main CLI entry point
├── feature-*.md           # Feature development plans
├── prompts/               # Template prompts
└── setup.sh               # Setup script
```

## Current Development Priorities

- Enhancing post-processing capabilities for trained models
- Improving configuration management UX
- Developing more efficient validation grid generation