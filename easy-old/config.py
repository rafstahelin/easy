#!/usr/bin/env python3
"""
Console-based JSON editor focusing on top-level keys,
with optional aliasing, optional filtered key list,
and now --keys for editing multiple keys sequentially,
PLUS --keys-with-values for direct key=value updates.

Features:
1. --alias-file <path>: Use short aliases for long JSON keys (optional).
2. --key <keyOrAlias>: Edit only that single top-level key (or alias) and exit.
3. --keys <k1> <k2> ...: Edit multiple top-level keys (or aliases) in sequence, then exit.
4. --options-file <path>: Show/edit only keys listed in this JSON file (must be a JSON array).
5. --keys-with-values keyOrAlias1=value1 keyOrAlias2=value2 ...
   Update multiple keys to the specified values directly, no prompt.

All edits auto-save.

Additionally:
- If --alias-file is not passed and "alias.json" exists in the same folder as this script, it is loaded automatically.
- If --options-file is not passed and "options.json" exists in the same folder as this script, it is loaded automatically.
"""

import argparse
import json
import os
import re
import time
from rich.console import Console
from rich.table import Table

def main():
    parser = argparse.ArgumentParser(
        description="Interactive top-level JSON editor using Rich (auto-save), with alias & subset filters."
    )
    parser.add_argument("filepath", help="Path to the JSON config file to edit.")
    parser.add_argument(
        "--key",
        help="If provided, only edit this single top-level key (or alias) and exit.",
        default=None
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        help="If provided, edit multiple top-level keys (or aliases) in sequence, then exit.",
        default=None
    )
    parser.add_argument(
        "--keys-with-values",
        nargs="+",
        help="If provided, update multiple keys (or aliases) to given values in 'key=value' format, then exit.",
        default=None
    )
    parser.add_argument(
        "--alias-file",
        help="Path to a JSON file with short aliases mapping to full JSON keys (optional).",
        default=None
    )
    parser.add_argument(
        "--options-file",
        help="Path to a JSON file containing an array of keys to display/edit in the menu (optional).",
        default=None
    )
    args = parser.parse_args()

    console = Console()

    # ------------------------------------------------------------------------
    # 0. Determine the script's directory
    # ------------------------------------------------------------------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = os.path.join(script_dir, "settings")

    # ------------------------------------------------------------------------
    # 1. Validate mutual exclusivity among --key, --keys, and --keys-with-values
    # ------------------------------------------------------------------------
    chosen_modes = [m for m in (args.key, args.keys, args.keys_with_values) if m]
    if len(chosen_modes) > 1:
        console.print(
            "[red]Cannot combine --key, --keys, or --keys-with-values. Use only one of these modes at a time.[/red]"
        )
        return

    # ------------------------------------------------------------------------
    # 2. Load alias file (either from user or config.alias.json in script folder)
    # ------------------------------------------------------------------------
    aliases = {}
    if args.alias_file:
        alias_file_path = args.alias_file
    else:
        possible_alias_path = os.path.join(script_dir, "config.alias.json")
        alias_file_path = possible_alias_path if os.path.isfile(possible_alias_path) else None

    if alias_file_path:
        try:
            with open(alias_file_path, "r", encoding="utf-8") as alias_f:
                aliases = json.load(alias_f)
                if not isinstance(aliases, dict):
                    console.print("[red]Alias file must be a JSON object (key/value pairs).[/red]")
                    return
        except Exception as e:
            console.print(f"[red]Error reading alias file '{alias_file_path}':[/red] {e}")
            return

    def resolve_key(key_or_alias: str) -> str:
        """Return the 'real' key if alias exists, else return the same string."""
        return aliases.get(key_or_alias, key_or_alias)

    # ------------------------------------------------------------------------
    # 3. Load options file (either from user or config.edit.json in script folder)
    # ------------------------------------------------------------------------
    if args.options_file:
        options_file_path = args.options_file
    else:
        possible_options_path = os.path.join(script_dir, "config.edit.json")
        options_file_path = possible_options_path if os.path.isfile(possible_options_path) else None

    options_keys = []
    if options_file_path:
        try:
            with open(options_file_path, "r", encoding="utf-8") as opts_f:
                raw = json.load(opts_f)
                if not isinstance(raw, list):
                    console.print("[red]Options file must be a JSON array of strings.[/red]")
                    return
                options_keys = [x for x in raw if isinstance(x, str)]
        except Exception as e:
            console.print(f"[red]Error reading options file '{options_file_path}':[/red] {e}")
            return

    # ------------------------------------------------------------------------
    # 4. Load main JSON config
    # ------------------------------------------------------------------------
    try:
        with open(args.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        console.print(f"[red]Error reading JSON file:[/red] {e}")
        return

    if not isinstance(data, dict):
        console.print("[red]This script only supports editing top-level dictionary keys.[/red]")
        return

    # ------------------------------------------------------------------------
    # Helper to parse a new value from string (try JSON else string)
    # ------------------------------------------------------------------------
    def parse_value(value_str: str):
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            return value_str

    # ------------------------------------------------------------------------
    # Helper to update a key in `data` and auto-save
    # ------------------------------------------------------------------------
    def update_key_value(real_key: str, old_value, new_value):
        """
        Update the given key in `data` to new_value, then auto-save the JSON.
        Also, if the user changed `--train_batch_size` to a value > 1,
        we adjust certain other fields accordingly by dividing them.
        """
        data[real_key] = new_value

        # --- Additional Logic: automatically adjust certain keys
        if real_key == "--train_batch_size" and isinstance(new_value, int) and new_value > 1:
            keys_to_divide = [
                "--max_train_steps",
                "--checkpointing_steps",
                "--checkpoints_total_limit",
                "--lr_warmup_steps",
            ]
            for k in keys_to_divide:
                if k in data and isinstance(data[k], int):
                    old_num = data[k]
                    new_num = max(1, old_num // new_value)
                    data[k] = new_num
                    console.print(
                        f"[blue]Automatically adjusted '{k}' from {old_num} to {new_num} because --train_batch_size is now {new_value}[/blue]"
                    )
        # --- End Additional Logic ---

        try:
            # json.dumps(data, indent=4)
            # Dump JSON to a string with indent
            json_str = json.dumps(data, indent=4)
            # If the key being edited is "learning_rate", reformat its value using regex.
            # if real_key == "--learning_rate":
            #     json_str = reformat_learning_rate(json_str,real_key)
            with open(args.filepath, "w", encoding="utf-8") as f:
                f.write(json_str)
            console.print(
                f"[green]Updated '{real_key}' from '{old_value}' to '{new_value}' and auto-saved.[/green]"
            )
        except Exception as e:
            console.print(f"[red]Error saving file:[/red] {e}")

    # ------------------------------------------------------------------------
    # Helper to edit a single key with a prompt
    # ------------------------------------------------------------------------
    def edit_single_key_prompt(real_key: str):
        old_value = data[real_key]
        console.print(
            f"\n[bold]Editing key:[/bold] [yellow]{real_key}[/yellow]\n"
            f"[bold]Current value:[/bold] {old_value}"
        )
        console.print("[bold green]Enter new value:[/bold green]")
        new_value_raw = console.input("> ").strip()
        new_value = parse_value(new_value_raw)
        update_key_value(real_key, old_value, new_value)

    # ------------------------------------------------------------------------
    # 5. Single-key mode: --key
    # ------------------------------------------------------------------------
    if args.key:
        real_key = resolve_key(args.key)
        if real_key not in data:
            console.print(f"[red]Key (or alias) '{args.key}' not found in JSON data.[/red]")
            return

        console.print(f"[bold cyan]Editing file:[/bold cyan] {args.filepath}")
        edit_single_key_prompt(real_key)
        console.print("[bold]Exiting editor (single key mode).[/bold]")
        return

    # ------------------------------------------------------------------------
    # 6. Multi-key mode: --keys (prompt each key)
    # ------------------------------------------------------------------------
    if args.keys:
        console.print(f"[bold cyan]Editing file: {args.filepath} (multiple keys mode)")
        for key_or_alias in args.keys:
            real_key = resolve_key(key_or_alias)
            if real_key not in data:
                console.print(f"[red]Key (or alias) '{key_or_alias}' not found in JSON data.[/red]")
                time.sleep(2)
                continue
            edit_single_key_prompt(real_key)
            time.sleep(1)
        console.print("[bold]Exiting editor (multi-key mode).[/bold]")
        return

    # ------------------------------------------------------------------------
    # 7. Multi-key mode with direct values: --keys-with-values
    # ------------------------------------------------------------------------
    if args.keys_with_values:
        console.print(f"[bold cyan]Editing file: {args.filepath} (keys-with-values mode)")
        for kv in args.keys_with_values:
            if '=' not in kv:
                console.print(f"[red]Invalid format: '{kv}' (expected 'key=value')[/red]")
                time.sleep(2)
                continue

            key_part, value_part = kv.split('=', 1)
            real_key = resolve_key(key_part.strip())
            if real_key not in data:
                console.print(f"[red]Key (or alias) '{key_part}' not found in JSON data.[/red]")
                time.sleep(2)
                continue

            old_value = data[real_key]
            new_value = parse_value(value_part.strip())
            update_key_value(real_key, old_value, new_value)
            time.sleep(1)

        console.print("[bold]Exiting editor (keys-with-values mode).[/bold]")
        return

    # ------------------------------------------------------------------------
    # 8. Otherwise, interactive menu (index from 1)
    # ------------------------------------------------------------------------
    while True:
        console.clear()
        console.print(f"[bold cyan]Editing: {args.filepath}")

        all_keys = list(data.keys())
        filtered_keys = [k for k in all_keys if (k in options_keys) or not options_keys]

        alias_map = {v: k for k, v in aliases.items()}
        title_str = "Top-level JSON Fields (Filtered)" if options_keys else "Top-level JSON Fields"
        table = Table(title=title_str, show_lines=True)
        table.add_column("Index", justify="right", style="bold magenta")
        table.add_column("Key", style="bold yellow")
        table.add_column("Alias", style="cyan")
        table.add_column("Value", style="white")

        for i, k in enumerate(filtered_keys, start=1):
            alias_str = alias_map.get(k, "")
            table.add_row(str(i), k, alias_str, str(data[k]))
        console.print(table)

        if not filtered_keys:
            console.print("[yellow]No keys to display. (Check options-file or JSON content.)[/yellow]")
            console.print("Type 'q' to quit.")
        else:
            console.print("\n[bold green]Enter an index to edit that field, or type 'q' to quit.[/bold green]")

        choice = console.input("> ").strip()
        if choice.lower() == "q":
            break

        if not choice.isdigit():
            console.print("[red]Invalid choice. Please enter an index number.[/red]")
            time.sleep(1)
            continue

        index = int(choice) - 1
        if index < 0 or index >= len(filtered_keys):
            console.print("[red]Index out of range. Try again.[/red]")
            time.sleep(1)
            continue

        key_to_edit = filtered_keys[index]
        edit_single_key_prompt(key_to_edit)
        time.sleep(2)

    console.print("[bold]Exiting editor.[/bold]")

if __name__ == "__main__":
    main()
