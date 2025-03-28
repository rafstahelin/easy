import os
import sys
from pathlib import Path
import traceback
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from time import sleep

class Tool:
    def __init__(self):
        print("Debug: Initializing Tool wrapper")
        try:
            self.console = Console()
            print("Debug: Console initialized")
            self.tool = ValidationGridTool()
            print("Debug: ValidationGridTool initialized")
        except Exception as e:
            print(f"Error in Tool initialization: {str(e)}")
            traceback.print_exc()
            raise
    
    def run(self):
        print("Debug: Tool.run() started")
        try:
            self.tool.run()
        except Exception as e:
            print(f"Error in tool.run(): {str(e)}")
            traceback.print_exc()
            input("Press Enter to continue...")  # Added pause
            raise

class ValidationGridTool:
    def __init__(self):
        print("Debug: Initializing ValidationGridTool")  # Debug line
        self.console = Console()
        
        # Initialize paths
        self.workspace_path = Path('/workspace/SimpleTuner')  # Changed from SimpleTrainer
        self.output_path = self.workspace_path / 'output'
        self.config_path = self.workspace_path / 'config'
        
        print(f"Debug: Paths initialized:")  # Debug line
        print(f"Debug: workspace_path = {self.workspace_path}")
        print(f"Debug: output_path = {self.output_path}")
        print(f"Debug: config_path = {self.config_path}")
        
        # Grid layout parameters
        self.top_margin = 240
        self.padding = 40
        self.title_height = 240
        self.image_title_height = 60
        self.main_title_font_size = 144
        self.image_title_font_size = 48

    def display_models(self, models: List[str]) -> None:
        """Display models in a 2-column grid layout."""
        # Create two columns of models
        table1 = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table1.add_column("Model", style="white", no_wrap=True)
        
        table2 = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table2.add_column("Model", style="white", no_wrap=True)
        
        # Split models into two columns
        mid_point = (len(models) + 1) // 2
        left_models = models[:mid_point]
        right_models = models[mid_point:]
        
        # Add models to first column
        for idx, model in enumerate(left_models, 1):
            table1.add_row(f"[yellow]{idx}.[/yellow] {model}")
        
        # Add models to second column
        for idx, model in enumerate(right_models, mid_point + 1):
            table2.add_row(f"[yellow]{idx}.[/yellow] {model}")
        
        # Create panel with both columns
        panel = Panel(
            Columns([table1, table2], equal=True, expand=True),
            title="[gold1]Available Models[/gold1]",
            border_style="blue"
        )
        self.console.print(panel)
        print()

    def display_versions(self, model: str, versions: List[str]) -> None:
        """Display versions in a 2-column grid layout."""
        # Create two columns of versions
        table1 = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table1.add_column("Version", style="white", no_wrap=True)
        
        table2 = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table2.add_column("Version", style="white", no_wrap=True)
        
        # Split versions into two columns
        mid_point = (len(versions) + 1) // 2
        left_versions = versions[:mid_point]
        right_versions = versions[mid_point:]
        
        # Add versions to first column
        for idx, version in enumerate(left_versions, 1):
            table1.add_row(f"[yellow]{idx}.[/yellow] {version}")
        
        # Add versions to second column
        for idx, version in enumerate(right_versions, mid_point + 1):
            table2.add_row(f"[yellow]{idx}.[/yellow] {version}")
        
        # Create panel with both columns
        panel = Panel(
            Columns([table1, table2], equal=True, expand=True),
            title=f"[gold1]{model} Versions[/gold1]",
            border_style="blue"
        )
        self.console.print(panel)
        print()

    def parse_image_info(self, filename: str) -> Tuple[int, str, Tuple[int, int]]:
        """Parse step number, concept, and resolution from filename."""
        pattern = r'step_(\d+)_(.+?)_(\d+)x(\d+)\.png'
        import re
        match = re.match(pattern, filename)
        if not match:
            raise ValueError(f"Invalid filename format: {filename}")
            
        step = int(match.group(1))
        concept = match.group(2)
        width = int(match.group(3))
        height = int(match.group(4))
        return step, concept, (width, height)

    def group_images(self, images: List[Path]) -> Dict[int, Dict[str, Path]]:
        """Group images by step and concept, excluding step_0."""
        groups: Dict[int, Dict[str, Path]] = {}
        
        for img_path in images:
            try:
                step, concept, _ = self.parse_image_info(img_path.name)
                if step == 0:  # Skip step_0 images
                    continue
                    
                if step not in groups:
                    groups[step] = {}
                groups[step][concept] = img_path
            except ValueError:
                continue
                
        return dict(sorted(groups.items(), reverse=True))

    def calculate_grid_dimensions(self, grouped_images: Dict[int, Dict[str, Path]]) -> Tuple[List[str], List[int], Tuple[int, int]]:
        if not grouped_images:
            raise ValueError("No valid images found for grid creation")
            
        all_concepts = list(dict.fromkeys(
            concept for step_images in grouped_images.values() 
            for concept in step_images.keys()
        ))
        
        steps = list(grouped_images.keys())
        
        first_image = next(iter(next(iter(grouped_images.values())).values()))
        sample_img = Image.open(first_image)
        base_size = sample_img.size
        
        return all_concepts, steps, base_size

    def scan_model_versions(self, model_name: str) -> list:
        """Scan for model versions in both output and config directories."""
        versions = set()
        
        output_model_path = self.output_path / model_name
        if output_model_path.exists():
            output_versions = [p.name for p in output_model_path.iterdir() 
                             if p.is_dir() and p.name != '.ipynb_checkpoints']
            versions.update(output_versions)
        
        config_versions = [
            p.name.split('-')[-1] for p in self.config_path.iterdir()
            if p.is_dir() and p.name.startswith(f"{model_name}-")
        ]
        versions.update(config_versions)
        
        return sorted(versions, key=lambda x: str(x))

    def create_grid(self, images: List[Path], model: str, version: str) -> Optional[Image.Image]:
        try:
            # Filter out corrupted images first
            valid_images = []
            for img_path in images:
                try:
                    # Attempt to open the image to verify it's valid
                    with Image.open(img_path) as test_img:
                        test_img.verify()  # Verify it's a valid image
                    valid_images.append(img_path)
                except Exception as e:
                    self.console.print(f"[yellow]Skipping corrupted image: {img_path.name} - {str(e)}[/yellow]")
            
            if not valid_images:
                self.console.print("[red]No valid images found after filtering corrupted files[/red]")
                return None
                
            # Continue with only valid images
            grouped_images = self.group_images(valid_images)
            if not grouped_images:
                self.console.print("[red]No valid grouped images found for grid creation[/red]")
                return None
                
            concepts, steps, (base_width, base_height) = self.calculate_grid_dimensions(grouped_images)
            
            n_cols = len(concepts)
            n_rows = len(steps)
            
            total_width = (base_width + self.padding) * n_cols + self.padding
            total_height = (
                self.top_margin +
                self.title_height +
                (base_height + self.image_title_height + self.padding) * n_rows +
                self.padding
            )
            
            grid_image = Image.new('RGB', (total_width, total_height), 'black')
            draw = ImageDraw.Draw(grid_image)
            
            try:
                main_title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                                self.main_title_font_size)
                image_title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                                    self.image_title_font_size)
            except Exception:
                main_title_font = ImageFont.load_default()
                image_title_font = ImageFont.load_default()
            
            main_title = f"{model}-{version} Validation Grid"
            title_bbox = draw.textbbox((0, 0), main_title, font=main_title_font)
            title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, self.padding), main_title, font=main_title_font, fill='white')
            
            start_y = self.top_margin + self.title_height
            for row, step in enumerate(steps):
                y = start_y + row * (base_height + self.image_title_height + self.padding)
                
                for col, concept in enumerate(concepts):
                    if concept in grouped_images[step]:
                        x = col * (base_width + self.padding) + self.padding
                        img_path = grouped_images[step][concept]
                        
                        title = f"Step {step} - {concept}"
                        title_bbox = draw.textbbox((0, 0), title, font=image_title_font)
                        title_width = title_bbox[2] - title_bbox[0]
                        title_x = x + (base_width - title_width) // 2
                        draw.text((title_x, y), title, font=image_title_font, fill='white')
                        
                        try:
                            with Image.open(img_path) as img:
                                # Make a copy to avoid issues with truncated files
                                img_copy = img.copy()
                                grid_image.paste(img_copy, (x, y + self.image_title_height))
                        except Exception as e:
                            self.console.print(f"[red]Error pasting image {img_path.name}: {str(e)}[/red]")
                            # Draw error placeholder
                            error_box = ImageDraw.Draw(grid_image)
                            error_box.rectangle(
                                [(x, y + self.image_title_height), 
                                (x + base_width, y + self.image_title_height + base_height)], 
                                outline="red", fill="black")
                            error_box.text(
                                (x + base_width // 2, y + self.image_title_height + base_height // 2),
                                "Image Error",
                                fill="red",
                                font=image_title_font,
                                anchor="mm"
                            )
            
            return grid_image
            
        except Exception as e:
            self.console.print(f"[red]Error creating grid: {str(e)}[/red]")
            traceback.print_exc()
            return None

    def save_grid(self, grid_image: Image.Image, model: str, version: str) -> bool:
        try:
            save_dir = self.config_path / f"{model}_{version}"
            save_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = save_dir / f"{model}_{version}-validation-grid.jpg"
            grid_image.save(output_path, 'JPEG', quality=95)
            
            self.console.print(f"[green]Grid saved to: {output_path}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error saving grid: {str(e)}[/red]")
            traceback.print_exc()
            return False

    def run(self):
        """Main execution method with debug logging"""
        while True:
            try:
                print("Debug: Starting run loop")  # Debug line
                
                # Verify paths exist
                if not self.output_path.exists():
                    print(f"Error: Output path does not exist: {self.output_path}")
                    return
                    
                if not self.config_path.exists():
                    print(f"Error: Config path does not exist: {self.config_path}")
                    return
                
                # Clear screen at start of each loop
                os.system('clear' if os.name == 'posix' else 'cls')
                self.console.print("[cyan]Loading tool: validation_grid[/cyan]")
                print()  # Add space after loading message
                
                # Scan for models
                models = [p.name for p in self.output_path.iterdir() 
                         if p.is_dir() and p.name != '.ipynb_checkpoints']
                
                if not models:
                    self.console.print("[red]No models found.[/red]")
                    sleep(1.5)
                    return
                models.sort()

                self.display_models(models)
                
                model_input = Prompt.ask("Select model number").strip()
                if not model_input:  # Empty input - exit to index
                    return
                    
                try:
                    model_idx = int(model_input) - 1
                    if not (0 <= model_idx < len(models)):
                        self.console.print("[red]Invalid selection.[/red]")
                        sleep(1.5)
                        continue
                except ValueError:
                    self.console.print("[red]Invalid input. Please enter a number.[/red]")
                    sleep(1.5)
                    continue
                
                selected_model = models[model_idx]
                
                versions = self.scan_model_versions(selected_model)
                if not versions:
                    self.console.print("[red]No versions found for selected model.[/red]")
                    sleep(1.5)
                    continue
                
                self.display_versions(selected_model, versions)
                
                version_input = Prompt.ask("Select version number").strip()
                if not version_input:  # Empty input - return to model selection
                    continue
                    
                try:
                    version_idx = int(version_input) - 1
                    if not (0 <= version_idx < len(versions)):
                        self.console.print("[red]Invalid version selection.[/red]")
                        sleep(1.5)
                        continue
                except ValueError:
                    self.console.print("[red]Invalid input. Please enter a number.[/red]")
                    sleep(1.5)
                    continue
                
                selected_version = versions[version_idx]
                
                validation_path = self.output_path / selected_model / selected_version / 'validation_images'

                if not validation_path.exists():
                    self.console.print(f"[red]No validation images found at: {validation_path}[/red]")
                    sleep(1.5)
                    continue
                
                images = list(validation_path.glob('*.png'))
                if not images:
                    self.console.print("[red]No validation images found.[/red]")
                    sleep(1.5)
                    continue
                
                self.console.print("[cyan]Creating validation grid...[/cyan]")
                grid_image = self.create_grid(images, selected_model, selected_version)
                
                if grid_image:
                    if self.save_grid(grid_image, selected_model, selected_version):
                        self.console.print("[green]Grid created and saved successfully![/green]")
                    else:
                        self.console.print("[red]Error saving grid image.[/red]")
                else:
                    self.console.print("[red]Error creating validation grid.[/red]")
                
                sleep(1.5)  # Brief pause to show status
                continue  # Return to model selection
                
            except Exception as e:
                self.console.print(f"[red]An error occurred: {str(e)}[/red]")
                traceback.print_exc()
                sleep(1.5)
                input("Press Enter to continue...")  # Added pause
                continue

if __name__ == "__main__":
    tool = Tool()
    tool.run()