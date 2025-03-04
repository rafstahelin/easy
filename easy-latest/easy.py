import sys
import time
import os
import json
import subprocess
from classes.response import Response
from classes.config import Config
from classes.multidatabackend import MultiDataBackend
from classes.userpromptlibrary import UserPromptLibrary

response = Response()

settings = None
try:
    with open("./settings/easy.json", "r", encoding="utf-8") as setting_f:
        settings = json.load(setting_f)        
except:
    response.print("Settings file not found", "e")
    sys.exit(0)

response.print(f"Settings loaded successfully","s")
time.sleep(1)

def find_folder(base_path, partial_name):
    try:
        for folder in os.listdir(base_path):
            if os.path.isdir(os.path.join(base_path, folder)) and partial_name in folder:
                return folder  # Return the first matching folder
    except FileNotFoundError:
        print(f"Error: Directory '{base_path}' not found.")
    
    return None  # Return None if no match is found


def init(args):

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
        options_file="./settings/options.json",
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
        sample_prompt_file_path=f"./prompts/{args[7]}.json"
    )

    if verify:
        upl.save()

    response.print(f"\n\nEasy init finished successfully folder: {final_config_folder}", "s")
    

def edit(args):
    response.console.clear()
    response.print("Easy edit\n-------------", "i")
    response.print(f"args: {args} ", "i")

def reinit(args):
    response.console.clear()
    response.print("Easy renit\n-------------", "i")
    response.print(f"args: {args} ", "i")

def listall(args):
    response.console.clear()
    response.print("Easy list\n-------------", "i")
    response.print(f"args: {args} ", "i")

def train(args):
    
    response.console.clear()
    response.print("Easy train\n-------------", "i")

    base_path = settings["config_folder_path"]
    name = args[0]

    config = find_folder(base_path, name)

    response.print(f"Training:  {config}", "i")

    process = subprocess.Popen(["bash", "train.sh",  settings['simple_tuner_path'], config], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stdout.decode())
    if stderr:
        print(stderr.decode(), file=sys.stderr)
    sys.exit(process.returncode)

def run():
    function_map = {
        "init": init,
        "reinit": reinit,
        "edit": edit,
        "train": train,
        "list": listall
    }

    if len(sys.argv) > 1:
        command = sys.argv[1]
        args = sys.argv[2:]  
        
        if command in function_map:
            function_map[command](args) if args else function_map[command]()  
        else:
            print(f"Unknown command: {command}")
    else:
        print("No arguments provided. Usage: easy <init|edit|reinit|train> [extra args]")

if __name__ == "__main__":
    run()