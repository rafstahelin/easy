import os
import sys
import platform
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn

class LoraSync:
    def __init__(self, base_path: Optional[Path] = None):
        self.console = Console()
        self.base_path = base_path or Path("/workspace/ComfyUI/models/loras/flux-train")
        self.dropbox_path = "dbx:/studio/ai/libs/diffusion-models/models/loras/flux-train"
        self.excluded_dirs = [".git", "__pycache__", ".vscode"]
        
    def clear_screen(self):
        """Clear the terminal screen."""
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")
    
    def verify_dropbox_connection(self) -> bool:
        """Verify that Dropbox is accessible."""
        try:
            # Quick dbx connection check
            result = subprocess.run(
                ["rclone", "lsf", "dbx:/", "--max-depth", "1"],
                check=True,
                capture_output=True,
                timeout=10
            )
            return True
        except subprocess.TimeoutExpired:
            self.console.print("[yellow]Warning: Dropbox connection check timed out. Will skip Dropbox uploads.[/yellow]")
            return False
        except subprocess.CalledProcessError:
            self.console.print("[yellow]Warning: Cannot connect to Dropbox. Will skip Dropbox uploads.[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[yellow]Warning when checking Dropbox connection: {str(e)}. Will skip Dropbox uploads.[/yellow]")
            return False
    
    def get_unique_families(self) -> Dict[str, List[Path]]:
        """Get unique family names and group configs by family."""
        families = {}
        
        # Check if the base directory exists
        if not self.base_path.exists():
            self.console.print(f"[red]Error: Path {self.base_path} does not exist[/red]")
            return families
            
        # List all subdirectories (families) in the base directory
        for family_dir in [d for d in self.base_path.iterdir() if d.is_dir() and d.name not in self.excluded_dirs]:
            family_name = family_dir.name
            
            # Find all configuration directories inside this family directory
            configs = []
            for config_dir in family_dir.iterdir():
                if config_dir.is_dir() and config_dir.name not in self.excluded_dirs:
                    configs.append(config_dir)
            
            if configs:
                families[family_name] = configs
        
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
    
    def sync_to_dropbox(self, family_name: str, config_path: Optional[Path] = None) -> bool:
        """Sync a model family or specific config to Dropbox using rclone sync."""
        try:
            # Check if Dropbox is accessible
            if not self.verify_dropbox_connection():
                self.console.print("[red]Cannot connect to Dropbox. Aborting sync.[/red]")
                return False
            
            if config_path:
                # Syncing a specific config
                source_path = str(config_path)
                dest_path = f"{self.dropbox_path}/{family_name}/{config_path.name}"
                self.console.print(f"[cyan]Syncing config: {config_path.name}[/cyan]")
            else:
                # Syncing an entire family
                source_path = str(self.base_path / family_name)
                dest_path = f"{self.dropbox_path}/{family_name}"
                self.console.print(f"[cyan]Syncing entire family: {family_name}[/cyan]")
            
            self.console.print(f"[cyan]From:[/cyan] {source_path}")
            self.console.print(f"[cyan]To:[/cyan] {dest_path}")
            
            # Using subprocess to run rclone sync
            cmd = [
                "rclone",
                "sync",
                "--progress",
                source_path,
                dest_path
            ]
            
            # Execute rclone and capture real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Show output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            if process.returncode == 0:
                self.console.print(f"[green]Successfully synced to Dropbox[/green]")
                return True
            else:
                self.console.print(f"[red]Failed to sync to Dropbox[/red]")
                return False
            
        except Exception as e:
            self.console.print(f"[red]Error syncing to Dropbox: {str(e)}[/red]")
            return False
    
    def process_family_configs(self, family_name: str, configs: List[Path]):
        """Process all configs in a family."""
        self.console.print(f"\n[cyan]Processing all configs for {family_name}...[/cyan]")
        
        # Use rclone sync to sync the entire family directory at once
        result = self.sync_to_dropbox(family_name)
        
        if result:
            self.console.print(f"[green]Successfully synced family {family_name} to Dropbox[/green]")
        else:
            self.console.print(f"[red]Failed to sync family {family_name} to Dropbox[/red]")
    
    def process_single_config(self, family_name: str, config_path: Path):
        """Process a single config."""
        self.console.print(f"\n[cyan]Processing config: {config_path.name}[/cyan]")
        result = self.sync_to_dropbox(family_name, config_path)
        
        if result:
            self.console.print(f"[green]Successfully synced config to Dropbox[/green]")
        else:
            self.console.print(f"[red]Failed to sync config to Dropbox[/red]")
    
    def run(self):
        """Run the LoRA sync tool with the two-step UI pattern."""
        self.clear_screen()
        self.console.print("[cyan]Loading tool: LoRA Sync[/cyan]")
        print()
        
        # Get and display unique family names
        family_groups = self.get_unique_families()
        if not family_groups:
            self.console.print("[red]No configuration families found in ComfyUI loras directory[/red]")
            input("\nPress Enter to continue...")
            return
        
        family_names = self.display_unique_families(family_groups)
        
        # Get family selection
        family_selection = input("\nEnter config family number (or press Enter to exit): ").strip()
        if not family_selection:
            return
        
        try:
            family_idx = int(family_selection) - 1
            if not (0 <= family_idx < len(family_names)):
                self.console.print("[red]Invalid selection[/red]")
                input("\nPress Enter to continue...")
                return
            
            selected_family = family_names[family_idx]
            
            # Show configs for selected family
            self.clear_screen()
            self.console.print("[cyan]Loading tool: LoRA Sync[/cyan]")
            print()
            
            family_configs = self.display_family_configs(selected_family, family_groups[selected_family])
            
            # Get config selection
            config_selection = input(f"\nEnter config number to process from {selected_family} (or press Enter to go back): ").strip()
            if not config_selection:
                return
            
            try:
                config_idx = int(config_selection)
                if config_idx == 1:  # "all" option
                    self.process_family_configs(selected_family, family_configs)
                elif 2 <= config_idx <= len(family_configs) + 1:  # +1 for "all" option
                    selected_config = family_configs[config_idx - 2]  # -2 to adjust for "all" and 0-indexing
                    self.process_single_config(selected_family, selected_config)
                else:
                    self.console.print("[red]Invalid selection[/red]")
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
        except ValueError:
            self.console.print("[red]Invalid input. Please enter a number.[/red]")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        sync = LoraSync()
        sync.run()
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        sys.exit(0)
    except Exception as e:
        console = Console(stderr=True)
        console.print(f"[red]Fatal error:[/red]")
        console.print(f"[red]{str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())
        input("Press Enter to exit...")