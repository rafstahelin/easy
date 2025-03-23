import os
import sys
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn

class LoraMover:
    def __init__(self, base_path: Optional[Path] = None):
        self.console = Console()
        self.base_path = base_path or Path("/workspace/SimpleTuner/output")
        self.comfy_path = Path("/workspace/ComfyUI/models/loras/flux-train")
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
    
    def extract_family_name(self, config_path: Path) -> str:
        """Extract the family name (prefix) from a config path."""
        # Extract just the base family name (e.g., "sofia" from "sofia_001_...")
        return config_path.name.split('_')[0] if '_' in config_path.name else config_path.name
    
    def get_unique_families(self) -> Dict[str, List[Path]]:
        """Get only unique family names (prefixes) and group configs by family."""
        families = {}
        
        # First, check if the output directory has family subdirectories
        for family_dir in [d for d in self.base_path.iterdir() if d.is_dir() and d.name not in self.excluded_dirs]:
            family_name = family_dir.name
            # Look for config directories inside the family directory
            configs = []
            for config_dir in family_dir.iterdir():
                if config_dir.is_dir():
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
    
    def show_progress(self, description: str, total: int = 100) -> None:
        """Show a progress bar with the given description."""
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green"),
            TaskProgressColumn(),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task(description, total=total)
            while not progress.finished:
                progress.update(task, advance=1)
                time.sleep(0.02)
    
    def upload_to_dropbox(self, renamed_file_path: Path, family_name: str, config_name: str) -> bool:
        """Upload a renamed file from ComfyUI directory to Dropbox."""
        try:
            # Construct the destination path in Dropbox exactly mirroring the ComfyUI path
            dbx_destination_dir = f"{self.dropbox_path}/{family_name}/{config_name}"
            
            self.console.print(f"[cyan]Uploading {renamed_file_path.name} to Dropbox...[/cyan]")
            
            # Using subprocess to run rclone
            try:
                # Use rclone to copy the file to Dropbox
                cmd = [
                    "rclone",
                    "copy",
                    "--progress",
                    str(renamed_file_path),
                    f"{dbx_destination_dir}"
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
                    self.console.print(f"[green]Successfully uploaded {renamed_file_path.name} to Dropbox[/green]")
                    return True
                else:
                    self.console.print(f"[red]Failed to upload {renamed_file_path.name} to Dropbox[/red]")
                    return False
                    
            except Exception as e:
                self.console.print(f"[red]Error uploading to Dropbox: {str(e)}[/red]")
                return False
            
        except Exception as e:
            self.console.print(f"[red]Error preparing Dropbox upload: {str(e)}[/red]")
            return False
    
    def move_lora_to_comfy(self, config_path: Path) -> bool:
        """Process all checkpoints from a config and move to ComfyUI with proper naming."""
        try:
            # Check if Dropbox is accessible
            dropbox_available = self.verify_dropbox_connection()
            
            # Find all checkpoint directories in the config directory
            checkpoints = [d for d in config_path.iterdir() if d.is_dir() and d.name.startswith("checkpoint-")]
            if not checkpoints:
                self.console.print(f"[red]No checkpoints found in {config_path}[/red]")
                return False
            
            # Get the family name from the parent directory
            family_name = self.extract_family_name(config_path.parent)
            config_name = config_path.name
            
            # Create the destination directory structure
            dest_dir = self.comfy_path / family_name / config_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Process each checkpoint and copy with appropriate naming
            processed_count = 0
            uploaded_count = 0
            
            for checkpoint_dir in sorted(checkpoints, key=lambda x: int(x.name.split("-")[1])):
                step_count = checkpoint_dir.name.split("-")[1]
                step_count = str(int(step_count)).zfill(5)
                
                # Look for safetensors file
                safetensor_path = checkpoint_dir / "pytorch_lora_weights.safetensors"
                if safetensor_path.exists():
                    # Create the target filename with the proper structure
                    new_filename = f"{family_name}_{config_name}_{step_count}.safetensors"

                    target_path = dest_dir / new_filename
                    
                    # Copy the file to ComfyUI
                    shutil.copy2(safetensor_path, target_path)
                    self.console.print(f"[green]Copied to {target_path}[/green]")
                    processed_count += 1
                    
                    # Upload the renamed file to Dropbox if connection is available
                    if dropbox_available:
                        if self.upload_to_dropbox(target_path, family_name, config_name):
                            uploaded_count += 1
            
            if processed_count > 0:
                self.show_progress("Processing complete", 100)
                self.console.print(f"[green]Successfully moved {processed_count} LoRAs to ComfyUI[/green]")
                if dropbox_available:
                    self.console.print(f"[green]Successfully uploaded {uploaded_count}/{processed_count} LoRAs to Dropbox[/green]")
                return True
            else:
                self.console.print("[yellow]No safetensor files found to process[/yellow]")
                return False
            
        except Exception as e:
            self.console.print(f"[red]Error moving LoRA: {str(e)}[/red]")
            return False
    
    def process_family_configs(self, family_name: str, configs: List[Path]):
        """Process all configs in a family."""
        self.console.print(f"\n[cyan]Processing all configs for {family_name}...[/cyan]")
        success_count = 0
        
        for config in configs:
            result = self.move_lora_to_comfy(config)
            if result:
                success_count += 1
        
        self.console.print(f"[green]Successfully processed {success_count}/{len(configs)} LoRAs to ComfyUI[/green]")
    
    def process_single_config(self, config_path: Path):
        """Process a single config."""
        self.console.print(f"\n[cyan]Processing config: {config_path.name}[/cyan]")
        result = self.move_lora_to_comfy(config_path)
        
        if result:
            self.console.print(f"[green]Successfully moved LoRA to ComfyUI[/green]")
        else:
            self.console.print(f"[red]Failed to move LoRA to ComfyUI[/red]")
    
    def run(self):
        """Run the LoRA mover tool with the two-step UI pattern."""
        self.clear_screen()
        self.console.print("[cyan]Loading tool: LoRA Mover[/cyan]")
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
            self.console.print("[cyan]Loading tool: LoRA Mover[/cyan]")
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
        mover = LoraMover()
        mover.run()
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