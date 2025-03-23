# Post-Process Bundle Implementation Plan

## Overview

This document outlines the strategy for implementing a bundled post-processing workflow (`easy pp`) that allows users to select a configuration once and apply multiple tools sequentially against that selection. The implementation will combine five existing tools:

1. LoRA Mover
2. Validation Grid
3. Dataset Grid
4. Download Config
5. Download Output (new tool to be developed)

## Goals

- Create a unified workflow with a single configuration selection
- Maintain backward compatibility for individual tool usage
- Establish a consistent selection pattern across all tools
- Minimize code duplication
- Design for future extensibility
- Implement a new Download Output tool for retrieving trained models

## Branching Strategy

```
main
  │
  └── feature/post-process-bundle
        │
        ├── step1-config-selector
        ├── step2-tool-refactoring
        ├── step3-lora-mover-update
        ├── step4-download-output-tool
        └── step5-bundle-orchestrator
```

We'll use a feature branch approach with granular commits:
- Create `feature/post-process-bundle` from `main`
- Develop in logical, testable increments
- Merge back to `main` once complete and tested

## Development Phases

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

## Testing Strategy

For each component:
1. **Unit Testing**: Test individual functions in isolation
2. **Integration Testing**: Test components working together
3. **End-to-End Testing**: Test the complete workflow
4. **Error Handling**: Deliberately introduce errors to verify recovery

## Contingency Planning

### Potential Issues

1. **Inconsistent configuration formats**: 
   - Solution: Add normalization in the ConfigSelector

2. **Tool-specific requirements**:
   - Solution: Allow tools to request additional parameters when needed

3. **Performance concerns with large datasets/models**:
   - Solution: Add progress indicators and optimize where possible

4. **Complex error scenarios**:
   - Solution: Implement robust logging and selective continuation

5. **Output directory structure variations**:
   - Solution: Add flexible path detection logic in Download Output tool

## Development Approach

We'll proceed with a back-and-forth iterative approach:
1. Discuss and refine each phase before implementation
2. Implement one component at a time
3. Review and test before moving to the next component
4. Address issues as they arise rather than waiting until the end

## Success Criteria

- All five tools can be run in sequence with a single configuration selection
- Individual tools still function correctly in standalone mode
- User experience is consistent across all tools
- Download Output tool correctly handles model selection criteria
- Code is well-structured and documented
- Error handling is robust
