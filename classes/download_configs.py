import os
import subprocess
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print as rprint

class Tool:
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/SimpleTuner/config')
        self.dropbox_base = "dbx:/studio/ai/data/1models"
        self.excluded_dirs = {'.ipynb_checkpoints', 'templates'}

    def verify_paths(self) -> bool:
        if not self.base_path.exists():
            rprint(f"[red]Error: Base config directory not found at {self.base_path}[/red]")
            return False
        try:
            result = self._run_rclone_command(["lsf", self.dropbox_base])
            if not result:
                return False
        except Exception as e:
            rprint(f"[red]Error checking Dropbox access: {str(e)}[/red]")
            return False
        return True

    def _run_rclone_command(self, args: List[str], check_output: bool = True) -> Optional[str]:
        try:
            cmd = ["rclone"] + args
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                rprint(f"[red]Rclone command failed: {result.stderr}[/red]")
                return None
            return result.stdout if check_output else ""
        except Exception as e:
            rprint(f"[red]Error running rclone command: {str(e)}[/red]")
            return None

    def find_matching_dropbox_folder(self, base_name: str) -> Optional[str]:
        result = self._run_rclone_command([
            "lsf", self.dropbox_base,
            "--dirs-only",
            "-R",
            "--max-depth", "1"
        ])
        
        if not result:
            return None

        matches = []
        for folder in result.splitlines():
            folder = folder.strip('/')
            if not folder:
                continue
                
            score = 0
            folder_lower = folder.lower()
            base_name_lower = base_name.lower().split("_")[0]
            
            if base_name_lower in folder_lower:
                score += 10
                if any(c.isdigit() for c in folder):
                    score += 5
                matches.append((score, folder))

        if matches:
            matches.sort(key=lambda x: (-x[0], len(x[1])))
            best_match = matches[0][1]
            rprint(f"[cyan]Found matching Dropbox folder: {best_match}[/cyan]")
            return best_match
            
        rprint(f"[yellow]No matching Dropbox folder found for {base_name}[/yellow]")
        return None

    def download_config(self, source_path: Path, base_name: str) -> bool:
        """Upload a config from RunPod (local) to Dropbox."""
        dropbox_folder = self.find_matching_dropbox_folder(base_name)
        if not dropbox_folder:
            return False

        # Create destination path in Dropbox
        dest_path = f"{self.dropbox_base}/{dropbox_folder}/4training/config/{source_path.name}"
        dest_path = dest_path.replace('//', '/')

        # Ensure the directory exists in Dropbox
        mkdir_result = self._run_rclone_command([
            "mkdir",
            f"{self.dropbox_base}/{dropbox_folder}/4training/config"
        ], check_output=False)
        
        if mkdir_result is None:
            return False

        # Copy from local (RunPod) to Dropbox
        rprint(f"[cyan]Copying {source_path.name} to {dest_path}[/cyan]")
        copy_result = self._run_rclone_command([
            "copy",
            "--checksum",
            str(source_path),   # Source is local RunPod path
            dest_path,          # Destination is Dropbox path
            "-v",
            "--progress",
            "--exclude", ".ipynb_checkpoints/**"
        ], check_output=False)
        
        if copy_result is not None:
            rprint(f"[green]Successfully uploaded {source_path.name} to Dropbox[/green]")
            return True
        return False

    def download_config_group(self, base_name: str) -> bool:
        """Upload all configs for a family from RunPod (local) to Dropbox."""
        dropbox_folder = self.find_matching_dropbox_folder(base_name)
        if not dropbox_folder:
            return False

        # Get all configs with the specified family name
        configs = list(self.base_path.glob(f"{base_name}_*"))
        if not configs:
            rprint(f"[yellow]No configs found matching {base_name}[/yellow]")
            return False

        # Upload each config to Dropbox
        success = True
        for config in configs:
            if not self.download_config(config, base_name):
                success = False
                rprint(f"[red]Failed to upload {config.name} to Dropbox[/red]")

        return success

    def extract_family_name(self, config_path: Path) -> str:
        """Extract the family name (prefix) from a config path."""
        # Extract the base family name (e.g., "sofia" from "sofia_001_...")
        return config_path.name.split('_')[0]
    
    def get_unique_families(self) -> Dict[str, List[Path]]:
        """Get only unique family names (prefixes) and group configs by family."""
        configs = [
            d for d in self.base_path.iterdir()
            if d.is_dir() and d.name not in self.excluded_dirs
        ]
        
        families = {}
        for config in configs:
            family_name = self.extract_family_name(config)
            if family_name not in families:
                families[family_name] = []
            families[family_name].append(config)
        return families

    def display_unique_families(self, families: Dict[str, List[Path]]) -> List[str]:
        """Display only unique family names in a two-column layout."""
        family_names = sorted(families.keys())
        
        # Create tables for two columns
        table1 = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table1.add_column("Family", style="white", no_wrap=True)
        
        table2 = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table2.add_column("Family", style="white", no_wrap=True)
        
        # Split families into two columns
        mid_point = (len(family_names) + 1) // 2
        left_families = family_names[:mid_point]
        right_families = family_names[mid_point:]
        
        # Add families to first column
        for idx, family in enumerate(left_families, 1):
            table1.add_row(f"[yellow]{idx}.[/yellow] {family}")
        
        # Add families to second column
        for idx, family in enumerate(right_families, mid_point + 1):
            table2.add_row(f"[yellow]{idx}.[/yellow] {family}")
        
        # Create panel with both columns
        panel = Panel(
            Columns([table1, table2], equal=True, expand=True),
            title="[gold1]Available Configurations[/gold1]",
            border_style="blue"
        )
        self.console.print(panel)
        
        return family_names

    def display_family_configs(self, family_name: str, configs: List[Path]) -> List[Path]:
        """Display all configs for a specific family in a two-column layout."""
        configs = sorted(configs, key=lambda x: x.name)
        
        # Create tables for two columns
        table1 = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table1.add_column("Config", style="white", no_wrap=True)
        
        table2 = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table2.add_column("Config", style="white", no_wrap=True)
        
        # First option is always "all"
        table1.add_row(f"[yellow]1.[/yellow] all")
        
        # Split configs into two columns (after accounting for "all")
        if len(configs) <= 7:
            # For small number of configs, keep them all in first column
            for idx, config in enumerate(configs, 2):
                table1.add_row(f"[yellow]{idx}.[/yellow] {config.name}")
        else:
            # For larger numbers, balance the columns
            mid_point = len(configs) // 2
            
            # Add first half to left column (after "all")
            for idx, config in enumerate(configs[:mid_point], 2):
                table1.add_row(f"[yellow]{idx}.[/yellow] {config.name}")
            
            # Add second half to right column
            start_idx = mid_point + 2  # +2 to account for "all" and 0-indexing
            for idx, config in enumerate(configs[mid_point:], start_idx):
                table2.add_row(f"[yellow]{idx}.[/yellow] {config.name}")
        
        # Create panel with both columns
        panel = Panel(
            Columns([table1, table2], equal=True, expand=True),
            title=f"[gold1]{family_name} Configs[/gold1]",
            border_style="blue"
        )
        self.console.print(panel)
        
        return configs

    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def run(self):
        self.clear_screen()
        
        if not self.verify_paths():
            return

        while True:
            try:
                self.console.print("[cyan]Loading tool: download_configs[/cyan]")
                print()
                
                # STEP 1: Show ONLY unique family names (prefixes)
                family_groups = self.get_unique_families()
                if not family_groups:
                    rprint("[yellow]No config directories found to process[/yellow]")
                    return
                    
                family_names = self.display_unique_families(family_groups)
                
                family_selection = input("\nEnter config family number (or press Enter to exit): ").strip()
                if not family_selection:
                    break
                
                try:
                    family_idx = int(family_selection) - 1
                    if not (0 <= family_idx < len(family_names)):
                        rprint("[red]Invalid selection[/red]")
                        input("\nPress Enter to continue...")
                        self.clear_screen()
                        continue
                    
                    selected_family = family_names[family_idx]
                    
                    # STEP 2: Show configs for selected family
                    self.clear_screen()
                    self.console.print("[cyan]Loading tool: download_configs[/cyan]")
                    print()
                    
                    family_configs = self.display_family_configs(
                        selected_family, 
                        family_groups[selected_family]
                    )
                    
                    config_selection = input(f"\nEnter config number to download from {selected_family} (or press Enter to go back): ").strip()
                    if not config_selection:
                        self.clear_screen()
                        continue
                    
                    try:
                        config_idx = int(config_selection)
                        if config_idx == 1:  # "all" option
                            self.download_config_group(selected_family)
                        elif 2 <= config_idx <= len(family_configs) + 1:  # +1 for "all" option
                            selected_config = family_configs[config_idx - 2]  # -2 to adjust for "all" and 0-indexing
                            self.download_config(selected_config, selected_family)
                        else:
                            rprint("[red]Invalid selection[/red]")
                    except ValueError:
                        rprint("[red]Invalid input. Please enter a number.[/red]")
                    
                    input("\nPress Enter to continue...")
                    self.clear_screen()
                    
                except ValueError:
                    rprint("[red]Invalid input. Please enter a number.[/red]")
                    input("\nPress Enter to continue...")
                    self.clear_screen()
                
            except KeyboardInterrupt:
                rprint("\n[yellow]Operation cancelled by user[/yellow]")
                break
            except Exception as e:
                rprint(f"[red]Error: {str(e)}[/red]")
                traceback.print_exc()
                input("\nPress Enter to continue...")
                self.clear_screen()

if __name__ == "__main__":
    try:
        downloader = Tool()
        downloader.run()
    except Exception as e:
        console = Console(stderr=True)
        console.print(f"[red]Fatal error:[/red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print(traceback.format_exc())
        input("Press Enter to exit...")