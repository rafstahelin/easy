# Core Classes Documentation

## Overview

Easy consists of several interconnected classes that work together to simplify the training workflow. This document provides detailed information about each core class and how they interact.

## Class: Config

**File:** `classes/config.py`

The Config class manages training configuration parameters. It handles creation, editing, and saving of training configuration files.

### Key Methods:

- `take_inputs()`: Collects configuration parameters through interactive prompts
- `load_files()`: Loads configuration templates and naming presets
- `editor()`: Provides an interactive editor for modifying configuration parameters
- `apply_name_preset()`: Applies naming conventions based on templates
- `save()`: Saves the configuration to a file

### Configuration Parameters:

The Config class manages all training parameters, including:
- Instance prompt
- Learning rate and scheduler
- Optimizer settings
- Batch size
- Training steps
- Checkpoint frequency

## Class: MultiDataBackend

**File:** `classes/multidatabackend.py`

This class manages the dataset configuration for training, handling multiple resolutions and dataset organization.

### Key Methods:

- `take_inputs()`: Collects dataset configuration parameters
- `resolve()`: Automatically configures dataset backends based on folder structure
- `edit()`: Allows editing of dataset configurations
- `save()`: Saves the dataset configuration to a file

### Features:

- Support for multiple resolutions
- Support for single datasets and subset datasets
- Automatic creation of appropriate backends for each resolution
- Configuration of text embedding caching

## Class: UserPromptLibrary

**File:** `classes/userpromptlibrary.py`

This class manages prompt templates used during training, allowing for standardized prompt formats with variable substitution.

### Key Methods:

- `take_inputs()`: Collects input parameters
- `update_config_data()`: Updates prompt templates with instance prompt
- `load_files()`: Loads prompt template files
- `save()`: Saves the configured prompt library

## Class: Response

**File:** `classes/response.py`

The Response class provides a consistent user interface for displaying information and collecting user input.

### Key Methods:

- `input()`: Displays a prompt and collects user input
- `print()`: Displays formatted text messages
- `edit_table()`: Displays data in a tabular format for editing

### Features:

- Color-coded output based on message type (info, error, success)
- Consistent formatting of tables and panels
- Rich text formatting using the rich library

## Class: LoRaMover

**File:** `classes/lora_mover.py`

The LoRaMover class handles the process of moving trained LoRA models from the SimpleTuner output directory to the ComfyUI models directory.

### Key Methods:

- `list_model_paths()`: Lists available model paths
- `list_model_versions()`: Lists available versions for a model
- `process_safetensors()`: Processes and renames safetensors files
- `process_single_version()`: Processes a single model version
- `process_all_versions()`: Processes all versions of a model
- `sync_to_dropbox()`: Syncs models to Dropbox

## Class: ValidationGridTool

**File:** `classes/validation_grid.py`

This class creates validation grids that compare model outputs across different checkpoints and prompts.

### Key Methods:

- `scan_model_versions()`: Scans for available model versions
- `create_grid()`: Creates a grid image from validation outputs
- `save_grid()`: Saves the grid image

### Features:

- Automated scanning of validation images
- Grid creation with proper labeling
- Support for multiple concepts and checkpoints

## Class: DatasetGridTool

**File:** `classes/dataset_grid.py`

This class creates visual grids of dataset images to help analyze training data.

### Key Methods:

- `list_config_folders()`: Lists available configuration folders
- `get_dataset_path()`: Extracts dataset path from config
- `create_grid()`: Creates a grid of dataset images
- `process_single_config()`: Processes a single configuration

## Class Relationships

Here's how the classes interact:

1. The main entry point (`easy.py`) calls the appropriate class based on the command.

2. For configuration initialization:
   - `Config` creates the base configuration
   - `MultiDataBackend` configures the dataset settings
   - `UserPromptLibrary` sets up the prompt templates

3. For training:
   - The `train()` function uses the configuration to launch training

4. For post-processing:
   - `LoRaMover` moves models to ComfyUI
   - `ValidationGridTool` creates validation grids
   - `DatasetGridTool` creates dataset grids
   - `LoraSync` syncs models to Dropbox

## Configuration Flow

1. User initiates configuration with `easy init`
2. `Config` class collects basic parameters
3. `Config.editor()` allows editing of training parameters
4. `Config.save()` saves the configuration
5. `MultiDataBackend` configures dataset settings
6. `MultiDataBackend.editor()` allows editing of dataset parameters
7. `MultiDataBackend.save()` saves the dataset configuration
8. `UserPromptLibrary` configures prompt templates
9. `UserPromptLibrary.save()` saves the prompt library

## Training and Post-Processing Flow

1. User initiates training with `easy train`
2. SimpleTuner training is launched with the configuration
3. Training produces models in the output directory
4. User runs post-processing with `easy pp`:
   - `LoRaMover` moves models to ComfyUI
   - `ValidationGridTool` creates validation grids
   - `DatasetGridTool` creates dataset grids
   - Configuration files are backed up
   - Models are synced to Dropbox