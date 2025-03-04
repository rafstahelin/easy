# Easy - Quick Start Guide

This guide will help you get started with Easy, a tool for simplifying LoRA model training workflows.

## Prerequisites

- [SimpleTuner](https://github.com/bghira/SimpleTuner) installed at `/workspace/SimpleTuner`
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) installed at `/workspace/ComfyUI`
- Python 3.8 or higher

## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/easy.git /workspace/easy
```

2. **Install dependencies:**

```bash
pip install -r /workspace/easy/requirements.txt
```

3. **Run setup script:**

```bash
bash /workspace/easy/setup.sh
```

## Basic Workflow

### 1. Prepare Your Dataset

Place your training images in a directory under the SimpleTuner datasets path:

```
/workspace/SimpleTuner/datasets/your_dataset_name/
```

Images should be high-quality, consistently cropped, and preferably around 1024px on the longest side.

### 2. Initialize a Configuration

```bash
easy init your_character_name 01 your_dataset_name default default lora "512,768,1024" default
```

Parameters:
- `your_character_name`: The instance prompt (what you're training)
- `01`: Version number
- `your_dataset_name`: Name of the dataset folder
- `default`: Scenario template to use
- `default`: Naming preset to use
- `lora`: ID base for the model
- `"512,768,1024"`: Resolutions to train at
- `default`: Prompt template to use

### 3. Edit Configuration (Optional)

You'll be presented with an interactive editor to adjust training parameters. Common edits include:

- Learning rate
- Training steps
- Batch size
- Checkpoint frequency

### 4. Start Training

```bash
easy train your_character_name
```

This will start the training process with the configuration you've created.

### 5. Monitor Training

Training progress is displayed in the terminal and can also be monitored through Weights & Biases if configured (`--report_to wandb`).

### 6. Process Trained Models

After training completes, process the models:

```bash
easy lm
```

This will move the trained models to your ComfyUI directory for use.

### 7. Create Validation Grids

```bash
easy vg
```

This creates visual grids comparing your model checkpoints with different prompts.

### 8. Full Post-Processing

To run all post-processing steps:

```bash
easy pp
```

This performs:
- Model moving to ComfyUI
- Configuration download/backup
- Validation grid creation
- Dataset grid creation

## Common Commands

```bash
# List configurations
easy list config

# List datasets
easy list datasets

# Edit an existing configuration
easy edit your_character_name config

# Edit dataset backend for a configuration
easy edit your_character_name backend

# Reinitialize a configuration with new parameters
easy reinit your_character_name new_name 02 new_dataset default lora "512,768,1024"

# Show help
easy help
```

## Tips for Best Results

1. **Quality Images**: Use consistent, high-quality images for training
2. **Training Steps**: Start with 2000-3000 steps for most cases
3. **Learning Rate**: The default of 1e-4 works well in most cases
4. **Batch Size**: Adjust based on GPU memory (1 is safe, increase if you have memory)
5. **Resolutions**: The 512,768,1024 combination works well for most cases

## Troubleshooting

- **Error loading configuration**: Check path in `easy.json`
- **Training fails to start**: Verify SimpleTuner installation and paths
- **Models not appearing in ComfyUI**: Check the `lora_mover.py` process output
- **Poor training results**: Try adjusting learning rate or increasing steps

## Next Steps

After completing this quick start, explore:
- Different scenario templates
- Custom prompt templates
- Advanced training parameters
- Dropbox integration for backup