# Claude System Instructions for ML Development Environment

## Environment Overview

You are assisting with development in a RunPod environment for ML model training and inference:

- **RunPod Instance**: Persistent storage GPU instance optimized for ML workloads
- **Environment**: Linux-based container with CUDA support
- **Development Interfaces**: SSH terminal, Jupyter Notebook, VSCode Server
- **Storage**: Network volume mounted to `/workspace` for persistence between sessions
- **GPU Access**: Direct access to NVIDIA GPUs for accelerated training and inference

## Project Architecture

This development environment hosts two complementary but independent repositories:

```
┌─────────────────┐                 ┌─────────────────┐
│ ML Training     │                 │ Inference & UI  │
│ ----------      │                 │ -----------     │
│ SimpleTuner     │────────────────▶│ ComfyUI         │
│ Easy (CLI)      │                 │ comfy-download  │
└─────────────────┘                 └─────────────────┘
```

### Related Projects

- `/workspace/easy/`: CLI wrapper for SimpleTuner training orchestration
- `/workspace/SimpleTuner/`: Core ML training framework (underlying engine)
- `/workspace/ComfyUI/`: Visual interface for model inference and testing
- `/workspace/comfy-download/`: ComfyUI workflow management and synchronization utilities

## Repository Access

You have access to the following repositories:

1. `rafstahelin/easy` - ML training orchestration CLI
2. `rafstahelin/comfy-download` - ComfyUI workflow management utilities

You can perform these operations:
- Read file contents
- Create branches
- Push files to branches

Limitations:
- Cannot create pull requests (PR creation fails with API errors)
- Single file update operations may fail

## Development Workflow Guidelines

### Two-Step Working Method

1. **Remote GitHub Workflow** (for larger features):
   - Create branch with descriptive name
   - Implement code and push to branch
   - User will manually create PR and pull locally for testing

2. **Local RunPod Workflow** (for quick fixes):
   - Generate code snippets for user to copy-paste
   - User will implement locally and test immediately 
   - User handles commits and PRs manually

### Code Style Guidelines

- Follow existing code style in each repository
- For Easy (Python): Clear variable names, docstrings, proper exception handling
- For comfy-download (Bash): POSIX compatibility, error handling, detailed logging

### UI Pattern for Easy CLI

When working with UI components in Easy CLI:
- Follow the standardized two-step configuration selection pattern
- Maintain consistent color scheme (panel border: blue, title: gold, numbering: yellow)
- Always include appropriate error handling and input validation

## Current Development Focus

### Easy Repository
- Enhancing post-processing capabilities for trained models
- Improving configuration management UX
- Developing more efficient validation grid generation

### comfy-download Repository
- Implementing security enhancements outlined in issue #5
- Optimizing workflow synchronization for large workflow directories
- Improving cron job management for automated tasks

## Testing Guidelines

- Test in isolation before integrating
- For Easy: Test with small step counts and minimal datasets
- For comfy-download: Test with small workflow files first
- Always check logs for errors and warnings
- Validate behavior across different configurations

## Context Retention

When discussing development across multiple sessions:
- Reference repository structure and key files
- Refer to `/workspace/easy/feature-Post-Process-Bundle.md` for current Easy development state
- For comfy-download, check issue #5 for security enhancement details