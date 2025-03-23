import os
import sys
import platform
import shutil
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn

class OutputDownloader:
    def __init__(self, base_path: Optional[Path] = None):
        self.console = Console()
        self.base_path = base_path or Path("/workspace/SimpleTuner/output")
        self.excluded_dirs = [".git", "__pycache__", ".vscode"]
        self.excluded_folders = ["validation_images"]
        self.excluded_files = ["pytorch_lora_weights.safetensors"]
        self.dropbox_base_path = "dbx:/studio/ai/data/1models"
        self.model_pattern = re.compile(r'013-([^/]+)')
        # Cache for model directory mappings
        self.model_dir_cache = {}
        
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
    
    def extract_family_name(self, config_path: Path) -> str:
        """Extract the family name (prefix) from a config path."""
        # Extract just the base family name (e.g., "sofia" from "sofia_001_...")
        return config_path.name.split('_')[0] if '_' in config_path.name else config_path.name
    
    def find_model_directory(self, family_prefix: str) -> Optional[str]:
        """
        Find the full model directory in Dropbox that corresponds to the family prefix.
        Returns the full path component (e.g., "013-ChuWong" for prefix "chu").
        """
        # Check cache first
        if family_prefix in self.model_dir_cache:
            return self.model_dir_cache[family_prefix]
        
        try:
            # List all directories in the models path
            result = subprocess.run(
                ["rclone", "lsf", self.dropbox_base_path, "--dirs-only"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Find directories matching the 013-* pattern
            model_dirs = result.stdout.strip().split('\n')
            matching_dirs = []
            
            for dir_name in model_dirs:
                # Skip empty lines
                if not dir_name:
                    continue
                
                # Check if this directory corresponds to our family prefix
                # This could involve checking if the prefix is in the directory name
                # or if there's another way to map between them
                if family_prefix.lower() in dir_name.lower():
                    matching_dirs.append(dir_name)
            
            if matching_dirs:
                # Use the first matching directory
                self.model_dir_cache[family_prefix] = matching_dirs[0]
                return matching_dirs[0]
            
            # If no exact match found, use a default pattern
            default_dir = f"013-{family_prefix}"
            self.console.print(f"[yellow]Warning: No matching model directory found for prefix '{family_prefix}'. Using '{default_dir}'.[/yellow]")
            self.model_dir_cache[family_prefix] = default_dir
            return default_dir
            
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not find model directory for '{family_prefix}': {str(e)}. Using default.[/yellow]")
            # Fall back to a default pattern
            default_dir = f"013-{family_prefix}"
            self.model_dir_cache[family_prefix] = default_dir
            return default_dir
    
    def get_unique_families(self) -> Dict[str, List[Path]]:
        """Get unique family names and group configs by family."""
        families = {}
        
        # Check if base directory exists
        if not self.base_path.exists():
            self.console.print(f"[red]Error: Path {self.base_path} does not exist[/red]")
            return families
        
        # First level is family directories
        for family_dir in [d for d in self.base_path.iterdir() 
                        if d.is_dir() and d.name not in self.excluded_dirs]:
            family_name = family_dir.name
            configs = []
            
            # Second level is config directories
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
    
    def get_highest_checkpoint(self, config_path: Path) -> Optional[Path]:
        """Find the highest checkpoint in a config directory."""
        checkpoints = [
            d for d in config_path.iterdir() 
            if d.is_dir() and d.name.startswith("checkpoint-")
        ]
        
        if not checkpoints:
            return None
        
        # Sort checkpoints by numeric value
        highest_checkpoint = sorted(
            checkpoints, 
            key=lambda x: int(x.name.split("-")[1])
        )[-1]
        
        return highest_checkpoint
    
    def create_filtered_temp_directory(self, config_path: Path) -> Tuple[Path, str]:
        """
        Create a temporary directory with filtered content.
        Returns the temp dir path and highest checkpoint number.
        """
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp())
        
        # Get highest checkpoint
        highest_checkpoint = self.get_highest_checkpoint(config_path)
        if not highest_checkpoint:
            raise ValueError(f"No checkpoints found in {config_path}")
        
        checkpoint_number = highest_checkpoint.name.split("-")[1]
        
        # Create the filtered content structure
        for item in config_path.iterdir():
            # Skip excluded folders
            if item.is_dir() and item.name in self.excluded_folders:
                continue
                
            # Skip lower checkpoints, only keep highest
            if item.is_dir() and item.name.startswith("checkpoint-"):
                if item != highest_checkpoint:
                    continue
            
            # Create a corresponding item in the temp directory
            dest_item = temp_dir / item.name
            
            if item.is_dir():
                # Copy directory, excluding the excluded files
                shutil.copytree(
                    item, 
                    dest_item,
                    ignore=lambda src, names: [
                        n for n in names if n in self.excluded_files
                    ]
                )
            elif item.is_file() and item.name not in self.excluded_files:
                # Copy file if not excluded
                shutil.copy2(item, dest_item)
        
        return temp_dir, checkpoint_number
    
    def cleanup_local_checkpoints(self, config_path: Path) -> bool:
        """Delete inferior checkpoints and safetensors files to save space."""
        try:
            # Find the highest checkpoint
            highest_checkpoint = self.get_highest_checkpoint(config_path)
            if not highest_checkpoint:
                self.console.print("[yellow]No checkpoints found to clean up[/yellow]")
                return False
                
            self.console.print(f"[cyan]Cleaning up inferior checkpoints in {config_path.name}...[/cyan]")
            
            # Get all checkpoints
            all_checkpoints = [
                d for d in config_path.iterdir() 
                if d.is_dir() and d.name.startswith("checkpoint-")
            ]
            
            # Delete all checkpoints except the highest one
            deleted_count = 0
            for checkpoint in all_checkpoints:
                if checkpoint != highest_checkpoint:
                    self.console.print(f"[yellow]Deleting inferior checkpoint: {checkpoint.name}[/yellow]")
                    shutil.rmtree(checkpoint)
                    deleted_count += 1
            
            # Delete the pytorch_lora_weights.safetensors file if it exists
            safetensors_file = config_path / "pytorch_lora_weights.safetensors"
            if safetensors_file.exists():
                self.console.print(f"[yellow]Deleting: pytorch_lora_weights.safetensors[/yellow]")
                safetensors_file.unlink()
                
            self.console.print(f"[green]Cleanup complete. Removed {deleted_count} inferior checkpoints.[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error during checkpoint cleanup: {str(e)}[/red]")
            return False

    def download_output_to_dropbox(self, config_path: Path) -> bool:
        """Download config output data to Dropbox with filtering applied."""
        try:
            # Check if Dropbox is accessible
            if not self.verify_dropbox_connection():
                self.console.print("[red]Cannot connect to Dropbox. Aborting download.[/red]")
                return False
                
            family_prefix = config_path.parent.name  # Get family name from parent directory
            config_name = config_path.name  # Get config name (without family prefix)
            
            # Find the model directory in Dropbox
            model_dir = self.find_model_directory(family_prefix)
            # Remove any trailing slashes to prevent double-slash errors
            model_dir = model_dir.rstrip('/')
            
            # Create filtered temp directory
            self.console.print(f"[cyan]Creating filtered copy of {config_path.name}...[/cyan]")
            temp_dir, checkpoint_number = self.create_filtered_temp_directory(config_path)
            
            # Keep the config name structure as it is
            # Format: dbx:/studio/ai/data/1models/013-ChuWong/4training/output/chu_001_constant1e4132
            dbx_destination_dir = f"{self.dropbox_base_path}/{model_dir}/4training/output/{family_prefix}_{config_name}"
            
            # Sync to Dropbox
            self.console.print(f"[cyan]Uploading filtered output to Dropbox: {dbx_destination_dir}[/cyan]")
            self.console.print(f"[cyan]Highest checkpoint: {checkpoint_number}[/cyan]")
            
            # Using subprocess to run rclone
            cmd = [
                "rclone",
                "copy",
                "--progress",
                str(temp_dir),
                dbx_destination_dir
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
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            success = process.returncode == 0
            if success:
                self.console.print(f"[green]Successfully uploaded output to Dropbox: {dbx_destination_dir}[/green]")
                
                # After successful upload, clean up inferior checkpoints
                self.cleanup_local_checkpoints(config_path)
                
                return True
            else:
                self.console.print(f"[red]Failed to upload to Dropbox[/red]")
                return False
            
        except Exception as e:
            self.console.print(f"[red]Error downloading output: {str(e)}[/red]")
            return False
    
    def process_family_configs(self, family_name: str, configs: List[Path]):
        """Process all configs in a family."""
        self.console.print(f"\n[cyan]Processing all configs for {family_name}...[/cyan]")
        success_count = 0
        
        for config in configs:
            result = self.download_output_to_dropbox(config)
            if result:
                success_count += 1
        
        self.console.print(f"[green]Successfully downloaded {success_count}/{len(configs)} config outputs to Dropbox[/green]")
    
    def process_single_config(self, config_path: Path):
        """Process a single config."""
        self.console.print(f"\n[cyan]Processing config: {config_path.name}[/cyan]")
        result = self.download_output_to_dropbox(config_path)
        
        if result:
            self.console.print(f"[green]Successfully downloaded output to Dropbox[/green]")
        else:
            self.console.print(f"[red]Failed to download output to Dropbox[/red]")
    
    def run(self):
        """Run the output downloader tool with the two-step UI pattern."""
        self.clear_screen()
        self.console.print("[cyan]Loading tool: Output Downloader[/cyan]")
        print()
        
        # Get and display unique family names
        family_groups = self.get_unique_families()
        if not family_groups:
            self.console.print("[red]No configuration families found in SimpleTuner output directory[/red]")
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
            self.console.print("[cyan]Loading tool: Output Downloader[/cyan]")
            print()
            
            family_configs = self.display_family_configs(selected_family, family_groups[selected_family])
            
            # Get config selection
            config_selection = input(f"\nEnter config number to download output from {selected_family} (or press Enter to go back): ").strip()
            if not config_selection:
                return
            
            try:
                config_idx = int(config_selection)
                if config_idx == 1:  # "all" option
                    self.process_family_configs(selected_family, family_configs)
                elif 2 <= config_idx <= len(family_configs) + 1:  # +1 for "all" option
                    selected_config = family_configs[config_idx - 2]  # -2 to adjust for "all" and 0-indexing
                    self.process_single_config(selected_config)
                else:
                    self.console.print("[red]Invalid selection[/red]")
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
        except ValueError:
            self.console.print("[red]Invalid input. Please enter a number.[/red]")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        downloader = OutputDownloader()
        downloader.run()
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