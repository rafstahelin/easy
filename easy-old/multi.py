#!/usr/bin/env python3

import argparse
import json
import os
import sys

def parse_json_value(value_str):
    """
    Attempt to parse the string as JSON so that
    numbers, booleans, null, arrays, etc. are handled.
    If that fails, we just return the raw string.
    """
    try:
        return json.loads(value_str)
    except json.JSONDecodeError:
        return value_str

def main():
    parser = argparse.ArgumentParser(description="Generate multi-backend JSON with multiple resolutions & a text-embeds backend.")
    parser.add_argument("--id-base",
                        help="Base string for the dataset ID. Final ID becomes 'id_{res}'.")
    parser.add_argument("--dataset-folder",
                        help="Used in instance_data_dir, cache paths, etc.")
    parser.add_argument("--res-repeats", nargs="+",
                        help="Pairs of resolution:repeats. E.g. 512:5 768:4 1024:3")
    parser.add_argument("--output-path", default=".",
                        help="Directory where 'multibackend.json' will be placed. (default: current dir)")

    # Global extra key=val pairs for all LoRA backends
    parser.add_argument("--lora-extra-args", nargs="*",
                        help="Optional extra key=value pairs applied globally to every LoRA backend. "
                             "Example: --lora-extra-args crop_aspect=random skip_file_discovery=vae")

    # New argument: per-resolution extra key=val pairs
    parser.add_argument("--per-res-lora-args", nargs="*",
                        help="Optional resolution-specific key=value pairs in 'RES:key=value' format. "
                             "Example: --per-res-lora-args 512:crop_aspect=random 512:skip_file_discovery=vae 768:some_extra=\"some value\"")

    args = parser.parse_args()

    # Prompt if missing (id_base, dataset_folder, etc.)
    if not args.id_base:
        args.id_base = input("Enter id-base (e.g. 'lora'): ").strip()
        if not args.id_base:
            print("id-base cannot be empty. Aborting.")
            sys.exit(1)

    if not args.dataset_folder:
        args.dataset_folder = input("Enter project name (e.g. 'amelia01-10'): ").strip()
        if not args.dataset_folder:
            print("dataset-folder cannot be empty. Aborting.")
            sys.exit(1)

    if not args.res_repeats:
        user_in = input("Enter resolution:repeat pairs (e.g. '512:5 768:4 1024:3'): ").strip()
        if not user_in:
            print("You must provide at least one resolution:repeats pair. Aborting.")
            sys.exit(1)
        args.res_repeats = user_in.split()

    # Build a dictionary from the global extra key=value pairs
    # We'll parse the values as JSON so that booleans, arrays, ints, etc. can be used.
    lora_extra_dict = {}
    if args.lora_extra_args:
        for kv in args.lora_extra_args:
            if '=' not in kv:
                print(f"ERROR: Extra arg '{kv}' is missing an '=' sign.", file=sys.stderr)
                sys.exit(1)
            key_str, val_str = kv.split('=', 1)
            # parse the value
            lora_extra_dict[key_str] = parse_json_value(val_str)

    # Build a dictionary of per-resolution extras:
    # e.g. 512:crop_aspect=random -> per_res_extras[512]["crop_aspect"] = "random"
    per_res_extras = {}
    if args.per_res_lora_args:
        for item in args.per_res_lora_args:
            if ':' not in item:
                print(f"ERROR: per-res arg '{item}' is missing a ':' separator (RES:key=value).", file=sys.stderr)
                sys.exit(1)

            # Split out the "RES" portion
            res_part, kv_part = item.split(':', 1)

            # Try to parse the resolution as int
            try:
                res_val = int(res_part)
            except ValueError:
                print(f"ERROR: '{res_part}' is not a valid integer resolution in '{item}'.", file=sys.stderr)
                sys.exit(1)

            # Now parse the "key=value" portion
            if '=' not in kv_part:
                print(f"ERROR: The portion '{kv_part}' is missing an '=' sign (RES:key=value).", file=sys.stderr)
                sys.exit(1)
            key_str, val_str = kv_part.split('=', 1)

            # Convert the val via JSON parse
            val_str_parsed = parse_json_value(val_str)

            # Store into the dictionary
            if res_val not in per_res_extras:
                per_res_extras[res_val] = {}
            per_res_extras[res_val][key_str] = val_str_parsed

    # Compose the final JSON filename under --output-path
    output_dir = os.path.abspath(args.output_path)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "multidatabackend.json")

    # If that file exists, confirm overwrite
    # if os.path.exists(output_file):
    #     confirm = input(f"File '{output_file}' already exists. Overwrite it? [y/N] ").strip().lower()
    #     if confirm not in ("y", "yes"):
    #         print("Aborting.")
    #         sys.exit(1)

    # Parse the resolution:repeat pairs into a list of dicts
    resolution_list = []
    for rr in args.res_repeats:
        # Expect something like "768:4"
        if ":" not in rr:
            print(f"ERROR: '{rr}' is not in 'res:repeats' format.", file=sys.stderr)
            sys.exit(1)
        res_str, rep_str = rr.split(":", 1)
        try:
            res_val = int(res_str)
            rep_val = int(rep_str)
        except ValueError:
            print(f"ERROR: Could not parse '{rr}' as 'int:int'.", file=sys.stderr)
            sys.exit(1)
        resolution_list.append({"res": res_val, "repeats": rep_val})

    # Build each LoRA backend
    def make_lora_backend(res, repeats):
        # Compose final ID like "lora_512"
        backend_id = f"{args.id_base}_{res}"
        # Basic structure
        backend = {
            "id": backend_id,
            "repeats": repeats,
            "instance_data_dir": f"datasets/{args.dataset_folder}",
            "cache_dir_vae": f"cache/vae/{args.dataset_folder}",
            "cache_file_suffix": f"-{args.id_base}_{res}",
            "crop": True,
            "crop_aspect": "closest",
            "crop_aspect_buckets": [0.7, 0.8, 0.87, 1.0],
            "resolution_type": "pixel_area",
            "resolution": res,
            "minimum_image_size": min(res, 256),
            "maximum_image_size": max(res, 512),
            "target_downsample_size": res,
            "prepend_instance_prompt": False,
            "only_instance_prompt": False,
            "caption_strategy": "textfile",
            "skip_file_discovery": "",
            "type": "local",
            "dataset_type": "image",
            "preserve_data_backend_cache": False,
            "disabled": False
        }
        # Merge in any user-specified extras (global)
        backend.update(lora_extra_dict)

        # Merge in per-resolution extras if any
        if res in per_res_extras:
            backend.update(per_res_extras[res])

        return backend

    # Text-embeds dataset
    def make_text_embeds_backend():
        return {
            "id": "text_embeds",
            "cache_dir": f"cache/text/{args.dataset_folder}",
            "dataset_type": "text_embeds",
            "default": True,
            "type": "local",
            "disabled": False,
            "write_batch_size": 128
        }

    # Build the entire list of dataset entries
    all_backends = []
    for item in resolution_list:
        res = item["res"]
        reps = item["repeats"]
        all_backends.append(make_lora_backend(res, reps))

    # Append text-embeds backend
    all_backends.append(make_text_embeds_backend())

    # Dump to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_backends, f, indent=4)

    print(f"Created '{output_file}' with {len(all_backends)} backends.")
    if lora_extra_dict:
        print("Global Extra LoRA fields added:")
        for k, v in lora_extra_dict.items():
            print(f"  {k}={v}")
    if per_res_extras:
        print("\nPer-resolution overrides:")
        for resolution, kv_dict in per_res_extras.items():
            print(f"  For resolution {resolution}:")
            for k, v in kv_dict.items():
                print(f"    {k}={v}")

if __name__ == "__main__":
    main()
