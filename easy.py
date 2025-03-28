import sys
import time
import os
import json
import subprocess
from pathlib import Path
from classes.response import Response
from classes.config import Config
from classes.multidatabackend import MultiDataBackend
from classes.userpromptlibrary import UserPromptLibrary

response = Response()

config_options_file_path = "/workspace/easy/settings/options.json"

settings = None
try:
    with open("/workspace/easy/settings/easy.json", "r", encoding="utf-8") as setting_f:
        settings = json.load(setting_f)
except Exception as e:
    response.print(f"Settings file not found or error reading settings:\n{e}", "e")
    sys.exit(0)

response.print(f"Settings loaded successfully", "s")
time.sleep(0.5)
response.console.clear()

def find_folder(base_path, partial_name):
    try:
        for folder in os.listdir(base_path):
            if os.path.isdir(os.path.join(base_path, folder)) and partial_name in folder:
                return folder
    except FileNotFoundError:
        response.print(f"Error: Directory '{base_path}' not found.", "e")
    except Exception as e:
        response.print(f"Error finding folder:\n{e}", "e")
    return None

def find_folders(base_path, partial_name):
    folders = []
    try:
        for folder in os.listdir(base_path):
            if partial_name:
                if os.path.isdir(os.path.join(base_path, folder)) and partial_name in folder:
                    folders.append(folder)
            else:
                folders.append(folder)
        folders.sort()
    except FileNotFoundError:
        response.print(f"Error: Directory '{base_path}' not found.", "e")
    except Exception as e:
        response.print(f"Error finding folders:\n{e}", "e")
    return folders


def init(args):
    try:
        response.console.clear()
        response.print("Easy init\n-------------", "i")

        config = Config()
        verify = config.take_inputs(
            instance_prompt=args[0],
            instance_prompt_version=args[1],
            dataset_folder=f"{settings['dataset_folder_path']}/{args[2]}",
            config_folder=settings["config_folder_path"],
            output_folder=settings["output_folder_path"],
            sample_config_file_path=f"{settings['scenario_folder_path']}/{args[3]}/config.json",
            options_file=config_options_file_path,
            naming_preset_file=f"{settings['names_folder_path']}/{args[4]}.json",
        )

        final_config_folder = None

        if verify:
            config.editor()
            final_config_folder = config.save()

        mdb = MultiDataBackend()

        verify = mdb.take_inputs(
            dataset_folder=f"{settings['dataset_folder_path']}/{args[2]}",
            config_folder=final_config_folder,
            id_base=args[5],
            resolutions=[int(value.strip()) for value in str(args[6]).split(",")]
        )

        if verify:
            mdb.resolve()
            mdb.editor()
            mdb.save()

        upl = UserPromptLibrary()
        verify = upl.take_inputs(
            instance_prompt=args[0],
            save_path=final_config_folder,
            sample_prompt_file_path=f"{settings['prompt_folder_path']}/{args[7]}.json"
        )

        if verify:
            upl.save()

        response.print(f"\n\nEasy init finished successfully folder: {final_config_folder}", "s")

    except Exception as e:
        response.print(f"Error in init:\n{e}", "e")
        sys.exit(1)


def edit(args):
    try:
        response.print("Easy edit\n-------------", "i")

        base_path = settings["config_folder_path"]
        ctype = args[1]
        name = args[0]  # Make sure you have this variable

        edit_folder = find_folder(base_path, name)
        if not edit_folder:
            response.print("Cannot find config folder to edit", "e")
            return

        if ctype == "config":
            config = Config()
            config.direct_editor(f"{base_path}/{edit_folder}/config.json", config_options_file_path)

        elif ctype == "backend":
            mdb = MultiDataBackend()
            mdb.direct_editor(f"{base_path}/{edit_folder}/multidatabackend.json", settings['dataset_folder_path'])
        else:
            response.print("Unknown edit type. Use 'config' or 'backend'.", "e")

    except Exception as e:
        response.print(f"Error in edit:\n{e}", "e")
        sys.exit(1)


def reinit(args):
    try:
        response.print("Easy reinit\n-------------", "i")

        base_path = settings["config_folder_path"]
        name = args[0]
        edit_folder = find_folder(base_path, name)

        if not edit_folder:
            response.print("Cannot find config folder", "e")
            return

        config_file_path = f"{base_path}/{edit_folder}/config.json"
        backend_file_path = f"{base_path}/{edit_folder}/multidatabackend.json"
        upl_file_path = f"{base_path}/{edit_folder}/user_prompt_library.json"

        config = Config()
        verify = config.take_inputs(
            instance_prompt=args[1],
            instance_prompt_version=args[2],
            dataset_folder=f"{settings['dataset_folder_path']}/{args[3]}",
            config_folder=settings["config_folder_path"],
            output_folder=settings["output_folder_path"],
            sample_config_file_path=config_file_path,
            options_file=config_options_file_path,
            naming_preset_file=f"{settings['names_folder_path']}/{args[4]}.json",
        )

        final_config_folder = None

        if verify:
            config.editor()
            final_config_folder = config.save()

        mdb = MultiDataBackend()

        verify = mdb.take_inputs(
            dataset_folder=f"{settings['dataset_folder_path']}/{args[3]}",
            config_folder=final_config_folder,
            id_base=args[5],
            resolutions=[int(value.strip()) for value in str(args[6]).split(",")]
        )

        if verify:
            mdb.resolve()
            mdb.editor()
            mdb.save()

        upl = UserPromptLibrary()
        verify = upl.take_inputs(
            instance_prompt=args[1],
            save_path=final_config_folder,
            sample_prompt_file_path=upl_file_path
        )

        if verify:
            upl.save()

        response.print(f"\n\nEasy reinit finished successfully folder: {final_config_folder}", "s")

    except Exception as e:
        response.print(f"Error in reinit:\n{e}", "e")
        sys.exit(1)


def lister(args):
    try:
        response.print("Easy list\n-------------", "i")

        ctype = args[0]
        group = args[1] if len(args) > 1 else None

        if ctype == "config":
            base_path = settings["config_folder_path"]
            folders = find_folders(base_path, group)
            for folder in folders:
                response.print(folder, "i")
        elif ctype == "datasets":
            base_path = settings['dataset_folder_path']
            folders = find_folders(base_path, group)
            for folder in folders:
                response.print(folder, "i")
        else:
            response.print("Unknown list type. Use 'config' or 'datasets'.", "e")

    except Exception as e:
        response.print(f"Error in list:\n{e}", "e")
        sys.exit(1)


def train(args):
    try:

        response.console.clear()
        response.print("Easy train\n-------------", "i")

        base_path = settings["config_folder_path"]
        name = args[0]

        config = find_folder(base_path, name)
        if not config:
            response.print("Cannot find config folder to train", "e")
            return

        response.print(f"Training:  {config}", "i")

        subprocess.run(["bash", "train.sh", settings['simple_tuner_path'], config])

    except Exception as e:
        response.print(f"Error in train:\n{e}", "e")
        sys.exit(1)


def help(args=None): 
    try:
        command_map = {
            "init": "<instance_prompt> <version> <dataset> <scenario> <naming_preset> <id_base> <resolutions> <prompt_file>",
            "edit": "<partial config folder name> <type(config/backend)>",
            "reinit": "<partial config folder name> <instance_prompt> <version> <dataset> <naming_preset> <id_base> <resolutions>",
            "list": "<config/datasets> [group]",
            "train": "<name>",
            "help": "Shows this help message",
            "lm": "LoRA mover (specific functionality not documented)",
            "ls": "LoRA sync (specific functionality not documented)",
            "dc": "Download configuration files",
            "vg": "Run validation grid",
            "dg": "Run dataset grid",
            "pp": "Run post process",
            "tpp": "Run train post process"
        }

        response.print("\n", "i")
        response.print("Available commands:\n", "i")

        for cmd, usage in command_map.items():
            response.print(f"[white]{cmd}[/white] {usage}", "i")

        response.print("\n", "i")

    except Exception as e:
        response.print(f"Error in help:\n{e}", "e")
        sys.exit(1)

def lora_mover():
    # Use the full path to the script
    script_path = str(Path(__file__).parent / "classes" / "lora_mover.py")
    response.print(f"Running lora_mover from {script_path}", "i")
    subprocess.run([sys.executable, script_path])

def lora_sync():
    # Use the full path to the script
    script_path = str(Path(__file__).parent / "classes" / "lora_sync.py")
    response.print(f"Running lora_sync from {script_path}", "i")
    subprocess.run([sys.executable, script_path])

def download_configs():
    # Use the full path to the script
    script_path = str(Path(__file__).parent / "classes" / "download_configs.py")
    response.print(f"Running download_configs from {script_path}", "i")
    subprocess.run([sys.executable, script_path])

def validation_grid():
    # Use the full path to the script
    script_path = str(Path(__file__).parent / "classes" / "validation_grid.py")
    response.print(f"Running validation_grid from {script_path}", "i")
    subprocess.run([sys.executable, script_path])

def dataset_grid():
    # Use the full path to the script
    script_path = str(Path(__file__).parent / "classes" / "dataset_grid.py")
    response.print(f"Running dataset_grid from {script_path}", "i")
    subprocess.run([sys.executable, script_path])

def post_process():
    lora_mover()
    download_configs()
    validation_grid()
    dataset_grid()

def train_post_process():
    train()
    lora_mover()
    download_configs()
    validation_grid()
    dataset_grid()

def run():
    try:
        function_map = {
            "init": init,
            "reinit": reinit,
            "edit": edit,
            "train": train,
            "list": lister,
            "help": help,
            "h": help,
            "lm": lora_mover,
            "ls": lora_sync,
            "dc": download_configs,
            "vg": validation_grid,
            "dg": dataset_grid,
            "pp": post_process,
            "tpp": train_post_process
        }

        if len(sys.argv) > 1:
            command = sys.argv[1]
            args = sys.argv[2:]
            
            if command in function_map:
                function_map[command](args) if args else function_map[command]()
            else:
                response.print(f"Unknown command: {command}", "e")
        else:
            response.print("No arguments provided. Usage: easy <init|edit|reinit|train|list|help> [extra args]", "e")
    except Exception as e:
        response.print(f"Error in run:\n{e}", "e")
        sys.exit(1)


if __name__ == "__main__":
    run()