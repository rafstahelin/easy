import argparse
import os
import json
import sys
import shutil
import time
import subprocess
from rich.console import Console
from rich.table import Table

def display_selection_table(options, title):
    console = Console()
    num_options = len(options)
    num_columns = 1
    if num_options > 8:
        num_columns = 2 if num_options <= 16 else 3

    table = Table(title=f"[bold cyan]{title}[/bold cyan]")
    for i in range(num_columns):
        table.add_column(f"Column {i + 1}", style="bold yellow")

    rows = []
    for i in range(0, num_options, num_columns):
        row = []
        for j in range(num_columns):
            idx = i + j
            if idx < num_options:
                row.append(f"[{idx + 1}] {options[idx]}")
            else:
                row.append("")
        rows.append(row)
    for row in rows:
        table.add_row(*row)

    console.print(table)

    while True:
        choice = console.input("[bold green]Enter index:[/bold green] ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        else:
            console.print("[red]Invalid choice. Try again.[/red]")

def load_json_file(file_path, console):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Failed to load {file_path}: {e}[/red]")
        return None

def get_subdirectories(directory):
    return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]

def select_option(arg_value, options, title, console):
    if arg_value in options:
        return arg_value
    return display_selection_table(options, title)

def rename_project_folder_from_config(console, project_folder_path, config_folder_path, names_folder_path, project_name, project_version):
    """
    Selects a names preset from the names folder, extracts values from the project config,
    joins them with underscores (removing dots), and renames the project folder accordingly.
    """
    if not os.path.isdir(names_folder_path):
        console.print(f"[red]Names folder path does not exist: {names_folder_path}[/red]")
        return

    names_files = [f for f in os.listdir(names_folder_path) if f.endswith('.json')]
    if not names_files:
        console.print(f"[red]No names preset JSON files found in: {names_folder_path}[/red]")
        return

    selected_names_file = display_selection_table(names_files, "Select a Names Preset")
    names_file_path = os.path.join(names_folder_path, selected_names_file)
    keys_to_collect = load_json_file(names_file_path, console)
    if not keys_to_collect:
        return

    config_file_path = os.path.join(project_folder_path, "config.json")
    project_config = load_json_file(config_file_path, console)
    if project_config is None:
        return

    values = []
    for key in keys_to_collect:
        # Get the value from config.json; default to empty string if not found.
        value = project_config.get(key, "")
        values.append(str(value).strip())
    # Join the values with underscores and remove any dots from the final name.
    new_project_name = "_".join(values).replace(".", "")
    new_project_version = f"{project_version}_{new_project_name}"
    new_project_name = f"{project_name}_{project_version}_{new_project_name}"
    new_project_folder_path = os.path.join(config_folder_path, new_project_name)
    try:
        os.rename(project_folder_path, new_project_folder_path)
        console.print(f"[green]Project folder renamed to: {new_project_folder_path}[/green]")
        return new_project_version, new_project_name , new_project_folder_path
    except Exception as e:
        console.print(f"[red]Failed to rename project folder: {e}[/red]")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="EA Utility: Gather project information and select dataset and scenario/config folders"
    )
    parser.add_argument("--project-name", help="Project name", default=None)
    parser.add_argument("--project-version", help="Project version", default=None)
    parser.add_argument("--dataset-folder", help="Dataset folder name", default=None)
    parser.add_argument("--scenario-folder", help="Scenario or Config folder name", default=None)
    parser.add_argument("--preset-name", help="Prompt preset name", default=None)
    # New argument: cpm (copy mode). If not provided, we will prompt the user.
    parser.add_argument("--cpm", help="Enter 1 to select from config folder path instead of scenario folder. Otherwise enter 0.", type=int)
    args = parser.parse_args()

    console = Console()
    settings_folder_path = os.path.join('./settings')
    settings_path = os.path.join(settings_folder_path, "easy.json")
    config_data = load_json_file(settings_path, console)
    if config_data is None:
        return

    dataset_folder_path = config_data.get("dataset_folder_path", "./datasets")
    scenario_folder_path = config_data.get("scenario_folder_path", "./scenario")
    config_folder_path = config_data.get("config_folder_path", "./config")
    prompt_folder_path = config_data.get("prompt_folder_path", "./prompts")
    names_folder_path = config_data.get("names_folder_path", "./names")

    # Get project name and version
    project_name = args.project_name or console.input("[bold green]Enter project name:[/bold green] ").strip()
    project_version = args.project_version or console.input("[bold green]Enter project version:[/bold green] ").strip()

    # Select dataset folder
    dataset_folders = get_subdirectories(dataset_folder_path)
    if not dataset_folders:
        console.print("[red]No folders found inside dataset directory.[/red]")
        return
    dataset_folder = select_option(args.dataset_folder, dataset_folders, "Select a Dataset Folder", console)

    # Determine copy mode (cpm)
    copy_mode = args.cpm
    if copy_mode is None:
        while True:
            mode_str = console.input("[bold green]Enter copy mode (0 for scenario folder, 1 for config folder):[/bold green] ").strip()
            if mode_str.isdigit() and int(mode_str) in (0, 1):
                copy_mode = int(mode_str)
                break
            else:
                console.print("[red]Invalid choice. Please enter 0 or 1.[/red]")

    # Select folder based on copy mode:
    if copy_mode == 1:
        selectable_folders = get_subdirectories(config_folder_path)
        if not selectable_folders:
            console.print("[red]No folders found inside config directory.[/red]")
            return
        selected_folder = select_option(args.scenario_folder, selectable_folders, "Select a Config Folder", console)
        folder_path_used = config_folder_path
    else:
        selectable_folders = get_subdirectories(scenario_folder_path)
        if not selectable_folders:
            console.print("[red]No folders found inside scenario directory.[/red]")
            return
        selected_folder = select_option(args.scenario_folder, selectable_folders, "Select a Scenario Folder", console)
        folder_path_used = scenario_folder_path

    console.print(f"Selected Folder: [yellow]{selected_folder}[/yellow]")
    console.print(f"Selected Dataset Folder: [yellow]{dataset_folder}[/yellow]")

    if not os.path.exists(os.path.join(folder_path_used, selected_folder)):
        console.print(f"[red]Selected folder does not exist: {os.path.join(folder_path_used, selected_folder)}[/red]")
        sys.exit(1)

    # Select prompt preset
    prompt_presets = [f for f in os.listdir(prompt_folder_path) if f.endswith('.json')]
    if not prompt_presets:
        console.print("[red]No prompt presets found inside prompt preset directory.[/red]")
        return
    selected_preset = args.preset_name if args.preset_name in prompt_presets else display_selection_table(prompt_presets, "Select a Prompt Preset")

    console.print(f"\n[bold cyan]Project Information:[/bold cyan]")
    console.print(f"Project Name: [yellow]{project_name}[/yellow]")
    console.print(f"Project Version: [yellow]{project_version}[/yellow]")
    console.print(f"Selected Dataset Folder: [yellow]{dataset_folder}[/yellow]")
    console.print(f"Selected Folder: [yellow]{selected_folder}[/yellow]")
    console.print(f"Selected Prompt Preset: [yellow]{selected_preset}[/yellow]")

    project_folder_name = f"{project_name}_{project_version}"
    project_folder_path = os.path.join(config_folder_path, project_folder_name)

    # Copy the selected folder (scenario or config) into the project folder.
    shutil.copytree(os.path.join(folder_path_used, selected_folder), project_folder_path, dirs_exist_ok=True)

    time.sleep(1)

    # Update prompt preset with project name substitutions
    preset_path = os.path.join(prompt_folder_path, selected_preset)
    prompt_data = load_json_file(preset_path, console)
    if prompt_data is None:
        return

    updated_prompt_data = {}
    for key, value in prompt_data.items():
        new_key = key.replace("{project_name}", project_name)
        new_value = value.replace("{project_name}", project_name)
        updated_prompt_data[new_key] = new_value

    prompt_library_path = os.path.join(project_folder_path, 'user_prompt_library.json')
    with open(prompt_library_path, 'w') as f:
        json.dump(updated_prompt_data, f, indent=4)
    console.print(f"[green]User Prompt Library created at: {prompt_library_path}[/green]")

    time.sleep(1)

    console.print("\n[bold green]Editing config.json[/bold green]")
    config_editor = os.path.join(os.path.dirname(__file__), 'config.py')
    config_vars = [
        "python",
        config_editor,
        os.path.join(project_folder_path, "config.json"),
        "--keys-with-values",
        f"instpr={project_name}",
        f"trkprj={project_name}",
        f"trkrun={project_name}_{project_version}",
        f"usprly=config/{project_name}_{project_version}/user_prompt_library.json",
        f"databc=config/{project_name}_{project_version}/multidatabackend.json",
        f"outdir=output/{project_name}/{project_name}_{project_version}"
    ]
    subprocess.run(config_vars)

    multidatabackend = os.path.join(os.path.dirname(__file__), 'multi.py')
    mdb_vars = [
        "python",
        multidatabackend,
        "--id-base", selected_folder,
        "--dataset-folder", f"{dataset_folder}",
        "--res-repeats", "512:5", "768:4", "1024:3",
        "--output-path", project_folder_path,
    ]
    subprocess.run(mdb_vars)

    config_vars = [
        "python",
        config_editor,
        os.path.join(project_folder_path, "config.json")
    ]
    subprocess.run(config_vars)

    # Final step: Rename project folder based on names preset keys from config.json.
    version_rename, rename, rename_path = rename_project_folder_from_config(console, project_folder_path, config_folder_path, names_folder_path, project_name, project_version)

    console.print("\n[bold green]Editing config.json[/bold green]")
    config_editor = os.path.join(os.path.dirname(__file__), 'config.py')
    config_vars = [
        "python",
        config_editor,
        os.path.join(rename_path, "config.json"),
        "--keys-with-values",
        f"trkrun={rename}",
        f"usprly=config/{rename}/user_prompt_library.json",
        f"databc=config/{rename}/multidatabackend.json",
        f"outdir=output/{project_name}/{version_rename}"
    ]
    subprocess.run(config_vars)

    multidatabackend = os.path.join(os.path.dirname(__file__), 'multi.py')
    mdb_vars = [
        "python",
        multidatabackend,
        "--id-base", selected_folder,
        "--dataset-folder", f"{dataset_folder}",
        "--res-repeats", "512:5", "768:4", "1024:3",
        "--output-path", rename_path,
    ]
    subprocess.run(mdb_vars)

    console.print(f"[green]Project folder created: {project_folder_path}[/green]")

if __name__ == "__main__":
    main()