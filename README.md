# Easy

Easy is a command-line tool that simplifies the workflow for training and managing LoRA models with [SimpleTuner](https://github.com/bghira/SimpleTuner). It provides a streamlined interface for configuring, training, and managing machine learning models, with a focus on diffusion models and integration with ComfyUI.

> **Note:** This repository is independent from the [comfy-download](https://github.com/rafstahelin/comfy-download) repository. If you need comfy-download functionality, please install it separately.

## Features

- **Simplified Configuration**: Easy setup of training configurations with interactive prompts
- **Dataset Management**: Tools for organizing and preparing datasets
- **Training Management**: Easily initiate and monitor training jobs
- **LoRA Model Management**: Tools for moving trained models to ComfyUI
- **Grid Visualization**: Create validation and dataset grids to compare results
- **Dropbox Integration**: Sync models and configs with Dropbox for backup and sharing

## Installation

### Prerequisites

- [SimpleTuner](https://github.com/bghira/SimpleTuner) installed at `/workspace/SimpleTuner`
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) installed at `/workspace/ComfyUI`
- Python 3.8 or higher

### Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- rich
- pillow
- safetensors
- numpy

### Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/easy.git /workspace/easy
```

2. Run the setup script:
```bash
cd /workspace/easy
bash setup.sh
```

## Project Structure

```
/workspace/easy/
├── easy.py                # Main script entry point
├── easy.bat               # Windows batch wrapper
├── easy.sh                # Linux/macOS shell wrapper
├── easy.json              # Main configuration file
├── classes/               # Core functionality classes
│   ├── config.py          # Training configuration management
│   ├── multidatabackend.py # Dataset configuration management
│   ├── userpromptlibrary.py # Prompt template management
│   ├── response.py        # UI response handling
│   ├── lora_mover.py      # LoRA model management tool
│   ├── lora_sync.py       # Dropbox sync tool
│   ├── validation_grid.py # Validation grid generation
│   ├── dataset_grid.py    # Dataset grid generation
│   └── download_configs.py # Config downloader tool
├── names/                 # Naming preset templates
├── prompts/               # Prompt templates
└── scenario/              # Training scenario templates
```

## Usage

Easy provides a command-line interface with several commands for managing the model training workflow.

### Basic Commands

```bash
# Initialize a new training configuration
easy init <instance_prompt> <version> <dataset> <scenario> <naming_preset> <id_base> <resolutions> <prompt_file>

# Edit an existing configuration
easy edit <partial config folder name> <type(config/backend)>

# Reinitialize a configuration with new parameters
easy reinit <partial config folder name> <instance_prompt> <version> <dataset> <naming_preset> <id_base> <resolutions>

# List available configurations or datasets
easy list <config/datasets> [group]

# Start training with a specific configuration
easy train <n>

# Show help information
easy help
```

### Advanced Commands

```bash
# LoRA Mover - Process and move trained models to ComfyUI
easy lm

# LoRA Sync - Sync models with Dropbox
easy ls

# Download configurations from Dropbox
easy dc

# Create validation grid for model checkpoints
easy vg

# Create dataset grid to visualize training data
easy dg

# Run post-processing tools (lm, dc, vg, dg)
easy pp

# Train and run post-processing tools
easy tpp
```

## Configuration

### Main Configuration (easy.json)

The `easy.json` file defines the paths to various components:

```json
{
    "simple_tuner_path": "/workspace/SimpleTuner",
    "config_folder_path": "/workspace/SimpleTuner/config",
    "scenario_folder_path": "/workspace/easy/scenario",
    "dataset_folder_path": "/workspace/SimpleTuner/datasets",
    "prompt_folder_path": "/workspace/easy/prompts",
    "names_folder_path": "/workspace/easy/names",
    "output_folder_path": "/workspace/SimpleTuner/output",
    "comfy_models_folder_path": "/workspace/ComfyUI/models"
}
```

### Training Configuration

Training configurations are created interactively and stored as JSON files. Key options include:

- Instance prompt
- Optimizer settings
- Learning rate and scheduler
- Batch size
- Training steps
- Checkpoint frequency

### Prompt Templates

Prompt templates are defined in JSON files in the `prompts/` directory and are used to generate formatted prompts for model training. Example:

```json
{
    "edgy_urban_fashion-{--instance_prompt}": "A bold and contemporary fashion editorial...",
    "resort_beachwear-{--instance_prompt}": "A luxurious resort fashion editorial...",
    "minimalist_high_fashion-{--instance_prompt}": "An avant-garde high fashion editorial...",
    "simple-{--instance_prompt}": "a midshotportrait of {--instance_prompt} in a simple setting...",
    "closeup-{--instance_prompt}": "a telephoto closeup portrait of {--instance_prompt}..."
}
```

## Workflow Example

A typical workflow using Easy would be:

1. Prepare your dataset in `/workspace/SimpleTuner/datasets/your_dataset`
2. Initialize a new configuration:
   ```bash
   easy init character_name 01 your_dataset default default lora "512,768,1024" default
   ```
3. Start training:
   ```bash
   easy train character_name
   ```
4. When training completes, move the models to ComfyUI:
   ```bash
   easy lm
   ```
5. Create validation grids to compare checkpoints:
   ```bash
   easy vg
   ```
6. Sync your models to Dropbox for backup:
   ```bash
   easy ls
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here]