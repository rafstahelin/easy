# AI Developer Guide for Easy CLI Project

## Overview

This guide outlines the recommended workflow for using AI assistants (like Claude) to help with development of the Easy CLI project. It explains how to effectively leverage AI capabilities while working around limitations.

## AI Assistant Development Workflows

There are two primary workflows when using AI to assist with development:

### 1. Remote GitHub-based Workflow

In this workflow, Claude directly modifies code in the GitHub repository:

1. **Branch Creation**: Claude creates a feature branch
   ```
   Claude creates a new branch using GitHub API
   ```

2. **Code Implementation**: Claude writes code and pushes it to the branch
   ```
   Claude implements code and pushes using GitHub API
   ```

3. **Manual PR Creation**: You create a PR from Claude's branch
   ```
   You manually create a PR in GitHub's interface
   ```

4. **Review & Merge**: You review Claude's changes and merge if satisfied

5. **Local Testing**: Pull the changes to your RunPod environment
   ```bash
   git fetch
   git checkout main
   git pull
   # Test the changes
   ```

**Limitations**:
- Claude cannot create PRs due to API issues
- Some file operations may fail through the GitHub API

### 2. Local RunPod-based Workflow

In this workflow, Claude generates code that you paste into your local environment:

1. **Requirement Discussion**: Discuss the feature or fix needed

2. **Code Generation**: Claude generates the necessary code

3. **Local Implementation**: You copy-paste the code to your RunPod environment
   ```bash
   cd /workspace/easy
   # Paste code into appropriate files
   ```

4. **Local Testing**: Test the changes directly
   ```bash
   ./easy.py [command] [options]
   ```

5. **Manual Commit**: If satisfied, commit and push the changes yourself
   ```bash
   git add .
   git commit -m "Description of changes"
   git push
   ```

**Advantages**:
- More direct control over code implementation
- Immediate testing feedback loop
- No API limitations

## Best Practices for AI Development

### 1. Contextual Information

When starting a new development session with Claude, provide:

- Link to the relevant repository
- Current feature branch being worked on
- Description of the task or feature
- References to any related issues or PRs

### 2. Code Review Prompting

When asking Claude to review code, provide:

- The file path
- The purpose of the code
- Specific aspects to focus on (performance, security, style, etc.)

### 3. Feature Implementation

When asking Claude to implement features:

- Break down complex features into smaller components
- Provide clear acceptance criteria
- Specify coding conventions to follow
- Reference similar existing features as examples

### 4. Testing Guidelines

When implementing tests:

- Specify which testing approach to use
- Provide sample test cases if possible
- Indicate how to verify the test works correctly

## Repository-Specific Guidelines

### Two-Step Configuration Selection UI

When working with the configuration selection UI:

- Follow the standardized two-step pattern (family selection → config selection)
- Maintain the specified color scheme and styling
- Always include an "all" option in the second step
- Properly handle error cases and edge conditions

### Post-Processing Features

When working on post-processing capabilities:

- Ensure compatibility with existing config organization
- Follow error handling patterns from existing tools
- Make sure any new commands are added to the help documentation
- Consider impacts on related systems (ComfyUI integration)

## Troubleshooting AI Integration

### GitHub API Issues

If Claude encounters issues with the GitHub API:

1. Verify the operation type (read vs. write)
2. Check the specific file paths being accessed
3. Consider falling back to the local workflow
4. For read-only operations, provide file contents directly in the chat

### Code Generation Issues

If Claude generates code that doesn't work:

1. Provide error messages and context
2. Ask for explanations of specific sections
3. Request alternative implementations
4. Break down complex requests into smaller parts