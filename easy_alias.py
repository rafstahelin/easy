#!/usr/bin/env python3
import os
import sys

def get_shell_config():
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return os.path.expanduser("~/.zshrc")
    elif "fish" in shell:
        return os.path.expanduser("~/.config/fish/config.fish")
    else:
        return os.path.expanduser("~/.bashrc")  # Default to bashrc

def add_alias(alias_name, script_path):
    if not os.path.isfile(script_path):
        print(f"Error: Script '{script_path}' not found.")
        sys.exit(1)

    config_file = get_shell_config()
    alias_command = f"alias {alias_name}='{script_path}'"

    # Check if alias already exists
    try:
        with open(config_file, "r") as file:
            content = file.read()
            if f"alias {alias_name}=" in content:
                print(f"Alias '{alias_name}' already exists in {config_file}")
                print(f"You need to source your shell config to use it: source {config_file}")
                return
    except FileNotFoundError:
        pass  # Config file doesn't exist yet, will be created

    # Add the alias
    with open(config_file, "a") as file:
        file.write(f"\n{alias_command}\n")
    
    print(f"Alias '{alias_name}' added to {config_file}")
    print("Applying changes...")
    os.system(f"source {config_file} 2>/dev/null || true")
    print("Setup complete! You can now use your alias.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python easy_alias.py <alias_name> <script_path>")
        sys.exit(1)
    
    alias_name = sys.argv[1]
    script_path = os.path.abspath(sys.argv[2])  # Convert to absolute path
    
    # Ensure the script is executable
    os.system(f"chmod +x {script_path}")
    add_alias(alias_name, script_path)