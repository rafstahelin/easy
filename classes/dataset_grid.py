import os
from pathlib import Path
from typing import List, Optional, Set, Dict
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.prompt import Prompt
from PIL import Image
import json
import math
import traceback

class DatasetGridTool:
    def __init__(self):
        self.console = Console()
        self.config_path = Path('/workspace/SimpleTuner/config')
        self.datasets_path = Path('/workspace/SimpleTuner/datasets')

    def extract_family_name(self, config_path: Path) -> str:
        """Extract the family name (prefix) from a config path."""
        # Extract just the base family name (e.g., "sofia" from "sofia_001_...")
        return config_path.name.split('_')[0]

    def get_unique_families(self) -> Dict[str, List[Path]]:
        """Get only unique family names (prefixes) and group configs by family."""
        folders = [f for f in self.config_path.iterdir() 
                  if f.is_dir() and f.name != 'templates' 
                  and not f.name.startswith('.ipynb_checkpoints')]
        
        # Group by family name
        families = {}
        for folder in folders:
            family_name = self.extract_family_name(folder)
            if family_name not in families:
                families[family_name] = []
            families[family_name].append(folder)
            
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
        """Display configs for a specific family in a 2-column layout."""
        # Sort configs
        family_configs = sorted(configs, key=lambda x: x.name)
        
        # Create tables for two columns
        table1 = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table1.add_column("Config", style="white", no_wrap=True)
        
        table2 = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table2.add_column("Config", style="white", no_wrap=True)
        
        # First option is always "all"
        table1.add_row(f"[yellow]1.[/yellow] all")
        
        # Split configs into two columns (after accounting for "all")
        if len(family_configs) <= 7:
            # For small number of configs, keep them all in first column
            for idx, config in enumerate(family_configs, 2):
                table1.add_row(f"[yellow]{idx}.[/yellow] {config.name}")
        else:
            # Calculate midpoint for balanced columns, accounting for "all" option
            mid_point = len(family_configs) // 2
            
            # Add first half to left column (after "all")
            for idx, config in enumerate(family_configs[:mid_point], 2):
                table1.add_row(f"[yellow]{idx}.[/yellow] {config.name}")
            
            # Add second half to right column
            start_idx = mid_point + 2  # +2 to account for "all" and 0-indexing
            for idx, config in enumerate(family_configs[mid_point:], start_idx):
                table2.add_row(f"[yellow]{idx}.[/yellow] {config.name}")
        
        # Create panel with both columns
        panel = Panel(
            Columns([table1, table2], equal=True, expand=True),
            title=f"[gold1]{family_name} Configs[/gold1]",
            border_style="blue"
        )
        self.console.print(panel)
        
        return family_configs

    def get_dataset_paths(self, config_dir: Path) -> List[Path]:
        """Extract all unique dataset paths from multidatabackend.json."""
        backend_file = config_dir / "multidatabackend.json"
        unique_paths = set()  # Use a set to store unique paths
        
        try:
            with open(backend_file) as f:
                data = json.load(f)
                for item in data:
                    if isinstance(item, dict) and 'instance_data_dir' in item and not item.get('disabled', False):
                        # Handle full path properly
                        full_path = item['instance_data_dir']
                        if full_path.startswith('datasets/'):
                            # Remove 'datasets/' prefix
                            rel_path = full_path[len('datasets/'):]
                        else:
                            rel_path = full_path

                        dataset_path = self.datasets_path / rel_path
                        if dataset_path.exists():
                            # Add to set to ensure uniqueness
                            unique_paths.add(dataset_path)
                        else:
                            self.console.print(f"[yellow]Warning: Path not found: {dataset_path}[/yellow]")
            
            # Convert set back to list for return
            paths = list(unique_paths)
            
            if paths:
                self.console.print(f"[green]Found {len(paths)} unique dataset paths[/green]")
            else:
                self.console.print("[red]No valid dataset paths found in config[/red]")
                
        except Exception as e:
            self.console.print(f"[red]Error reading dataset paths: {str(e)}[/red]")
            
        return paths

    def create_grid(self, images: List[Path], output_path: Path, title: str):
        """Create and save image grid."""
        pil_images = []
        for img_path in images:
            try:
                img = Image.open(img_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                pil_images.append(img)
            except Exception as e:
                self.console.print(f"[red]Error loading {img_path}: {str(e)}[/red]")

        if not pil_images:
            return

        n = len(pil_images)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

        cell_width = 512
        cell_height = 512
        title_height = 60

        grid = Image.new('RGB', 
                        (cols * cell_width, rows * cell_height + title_height),
                        'white')

        for idx, img in enumerate(pil_images):
            row = idx // cols
            col = idx % cols
            img.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
            
            x = col * cell_width
            y = row * cell_height + title_height
            grid.paste(img, (x, y))

        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(grid)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        draw.text((grid.width//2, title_height//2), title, 
                  fill='black', font=font, anchor="mm")

        quality = 95
        while True:
            test_path = output_path.with_suffix('.tmp.jpg')
            grid.save(test_path, 'JPEG', quality=quality)
            if test_path.stat().st_size <= 15_000_000 or quality <= 30:
                test_path.rename(output_path)
                break
            quality -= 5

    def find_images_recursively(self, directory: Path) -> List[Path]:
        """Find all images in a directory and its subdirectories."""
        images = []
        image_extensions = {'.jpg', '.jpeg', '.png'}
        
        # Add progress indication
        self.console.print(f"[cyan]Scanning directory: {directory}[/cyan]")
        
        # Walk through directory recursively
        for item in directory.rglob('*'):
            if item.is_file() and item.suffix.lower() in image_extensions:
                images.append(item)
                
        if images:
            self.console.print(f"[green]Found {len(images)} images in {directory} and subdirectories[/green]")
        else:
            self.console.print(f"[yellow]No images found in {directory} and subdirectories[/yellow]")
            
        return images

    def process_single_config(self, config_dir):
        dataset_paths = self.get_dataset_paths(config_dir)
        if not dataset_paths:
            self.console.print("[red]Could not find any valid dataset paths in config[/red]")
            return

        # Collect images from all dataset paths
        all_images = []
        for dataset_dir in dataset_paths:
            # First check if there are images directly in the directory
            direct_images = list(dataset_dir.glob("*.jpg")) + \
                           list(dataset_dir.glob("*.jpeg")) + \
                           list(dataset_dir.glob("*.png"))
            
            # Check for subdirectories with images
            has_subdirs = any(item.is_dir() for item in dataset_dir.iterdir())
            
            # If we have subdirectories and not many direct images, use recursive scanning
            if has_subdirs and len(direct_images) < 10:
                self.console.print(f"[cyan]Dataset {dataset_dir.name} has subdirectories. Using recursive scanning...[/cyan]")
                path_images = self.find_images_recursively(dataset_dir)
            else:
                path_images = direct_images
                self.console.print(f"[cyan]Found {len(path_images)} images directly in dataset folder {dataset_dir.name}[/cyan]")
                
            all_images.extend(path_images)

        if not all_images:
            self.console.print("[red]No images found in any dataset directories[/red]")
            return

        # Limit to first 100 images to prevent huge grids
        if len(all_images) > 100:
            self.console.print(f"[yellow]Limiting grid to first 100 of {len(all_images)} images[/yellow]")
            all_images = all_images[:100]

        output_file = config_dir / f"{config_dir.name}-dataset-grid.jpg"
        title = f"{config_dir.name} - dataset_grid"
        
        self.console.print("[cyan]Creating dataset grid...[/cyan]")
        self.create_grid(all_images, output_file, title)
        self.console.print(f"[green]Grid saved to: {output_file}[/green]")

    def process_family_configs(self, family_name: str, configs: List[Path]):
        """Process all configs in a family."""
        for config in configs:
            self.console.print(f"[cyan]Processing {config.name}...[/cyan]")
            self.process_single_config(config)

    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def run(self):
        self.clear_screen()
        self.console.print("[cyan]Loading tool: dataset_grid[/cyan]")
        print()
        
        try:
            # Step 1: Get and display unique family names
            family_groups = self.get_unique_families()
            
            if not family_groups:
                self.console.print("[red]No configuration folders found[/red]")
                return
            
            family_names = self.display_unique_families(family_groups)
            
            # Get selection for family
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
                
                # Step 2: Display configs for selected family
                self.clear_screen()
                self.console.print("[cyan]Loading tool: dataset_grid[/cyan]")
                print()
                
                family_configs = self.display_family_configs(selected_family, family_groups[selected_family])
                
                # Get selection for config
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
                        input("\nPress Enter to continue...")
                        
                except ValueError:
                    self.console.print("[red]Invalid input. Please enter a number.[/red]")
                    input("\nPress Enter to continue...")
                
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
                input("\nPress Enter to continue...")
                
        except Exception as e:
            self.console.print(f"[red]An error occurred: {str(e)}[/red]")
            traceback.print_exc()
            input("Press Enter to continue...")

class Tool:
    def __init__(self):
        self.tool = DatasetGridTool()
    
    def run(self):
        self.tool.run()

if __name__ == "__main__":
    tool = Tool()
    tool.run()