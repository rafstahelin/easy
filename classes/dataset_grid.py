import os
from pathlib import Path
from typing import List, Optional, Set
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.prompt import Prompt
from PIL import Image
import json
import math

class DatasetGridTool:
    def __init__(self):
        self.console = Console()
        self.config_path = Path('/workspace/SimpleTuner/config')
        self.datasets_path = Path('/workspace/SimpleTuner/datasets')

    def list_config_folders(self) -> List[str]:
        """List configuration folders grouped by base name."""
        folders = [f for f in self.config_path.iterdir() 
                  if f.is_dir() and f.name != 'templates' 
                  and not f.name.startswith('.ipynb_checkpoints')]
        
        grouped = {}
        ordered_folders = []
        panels = []
        index = 1
        
        for folder in folders:
            base_name = folder.name.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(folder.name)
            
        for base_name in sorted(grouped.keys()):
            content = []
            names_in_group = sorted(grouped[base_name], key=str.lower, reverse=True)
            
            # Add "process all" option for each group
            content.append(f"[yellow]{index}.[/yellow] all")
            ordered_folders.append(f"{base_name}:all")
            index += 1
            
            # Add individual folders
            for name in names_in_group:
                content.append(f"[yellow]{index}.[/yellow] {name}")
                ordered_folders.append(name)
                index += 1
                
            panel = Panel(
                "\n".join(content),
                title=f"[yellow]{base_name}[/yellow]",
                border_style="blue",
                width=40
            )
            panels.append(panel)
        
        for i in range(0, len(panels), 3):
            row_panels = panels[i:i + 3]
            self.console.print(Columns(row_panels, equal=True, expand=True))
            
        return ordered_folders

    def get_dataset_paths(self, config_dir: Path) -> List[Path]:
        """Extract all dataset paths from multidatabackend.json."""
        backend_file = config_dir / "multidatabackend.json"
        paths = []
        
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
                            paths.append(dataset_path)
                        else:
                            self.console.print(f"[yellow]Warning: Path not found: {dataset_path}[/yellow]")
            
            if paths:
                self.console.print(f"[green]Found {len(paths)} dataset paths[/green]")
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

    def run(self):
        config_folders = self.list_config_folders()
        if not config_folders:
            self.console.print("[red]No configuration folders found[/red]")
            return

        from rich.prompt import Prompt  # Change back to regular Prompt
        folder_num = Prompt.ask("Enter number to select config").strip()
        if not folder_num:
            return

        try:
            selected = config_folders[int(folder_num) - 1]
            
            # Handle "all" selection for a group
            if ":all" in selected:
                base_name = selected.split(":")[0]
                group_configs = [f for f in config_folders 
                               if f.startswith(base_name) and ":all" not in f]
                
                for config in group_configs:
                    self.console.print(f"[cyan]Processing {config}...[/cyan]")
                    config_dir = self.config_path / config
                    self.process_single_config(config_dir)
            else:
                config_dir = self.config_path / selected
                self.process_single_config(config_dir)
                
        except (ValueError, IndexError):
            self.console.print("[red]Invalid selection[/red]")
            return

class Tool:
    def __init__(self):
        self.tool = DatasetGridTool()
    
    def run(self):
        self.tool.run()

if __name__ == "__main__":
    tool = Tool()
    tool.run()