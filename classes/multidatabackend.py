import os
import time
import json
import ast
from .response import Response

def parse_value(value):
    """
    Attempt to parse the input into its most appropriate data type.
    """
    if isinstance(value, str):
        lower_value = value.lower()
        
        # Handle booleans
        if lower_value == "true":
            return True
        elif lower_value == "false":
            return False
        
        # Handle None
        if lower_value == "none":
            return None
        
        # Try integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try parsing lists, dicts, tuples safely
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, (list, tuple, dict)):
                return parsed
        except (ValueError, SyntaxError):
            pass
    
    # If input is already a dict (JSON-like object), return it as-is
    if isinstance(value, dict):
        return value
    
    # Default to string
    return value


class MultiDataBackend:

    def __init__(self):

        self.dataset_folder = None
        self.config_folder = None
        self.id_base = None
        self.resolutions = None

        self.subset_mode = 0

        self.response = Response()
        self.multidatabackend = {}

    def get_text_embeds(self, idx, folder):

        embed = {
            "id": f"{idx}",
            "cache_dir": f"cache/text/{folder}",
            "dataset_type": "text_embeds",
            "default": True,
            "type": "local",
            "disabled": False,
            "write_batch_size": 128
        }

        return embed

    def create_block(self, idx="", folder="", resolution=0): 

        block = {
            "id": f"{idx}",
            "repeats": 0,
            "instance_data_dir": f"datasets/{folder}",
            "cache_dir_vae": f"cache/vae/{folder}/{idx}",
            "cache_file_suffix": f"-{idx}",
            "crop": True,
            "crop_aspect": "closest",
            "crop_aspect_buckets": [
                0.7,
                0.8,
                0.87,
                1.0
            ],
            "resolution_type": "pixel_area",
            "resolution": resolution,
            "minimum_image_size": 256,
            "maximum_image_size": resolution,
            "target_downsample_size": resolution,
            "prepend_instance_prompt": True,
            "only_instance_prompt": False,
            "caption_strategy": "textfile",
            "skip_file_discovery": "",
            "type": "local",
            "dataset_type": "image",
            "preserve_data_backend_cache": False,
            "disabled": False
        }

        return block

    def add_backend_block(self, key, block):
        self.multidatabackend[key] = block
        self.response.print(f"Updated block {key}",'s')   
        time.sleep(0.5)

    def remove_backend_block(self, key):    
        if key in self.multidatabackend:
            del self.multidatabackend[key]
            self.response.print(f"Deleted block with key: {key}",'s')   

    def add_backend_block_data(self, block_id, key, value):
        self.multidatabackend[block_id][key] = parse_value(value)
        self.response.print(f"Updated key {key} in block {block_id}: {value}",'s')   
        time.sleep(0.5)

    def remove_backend_block_data(self, block_id, key):    
        if block_id in self.multidatabackend:
            del self.multidatabackend[block_id][key]
            self.response.print(f"Deleted key {key} in block {block_id}",'s')   

    def take_inputs(self, config_folder=None, id_base=None, dataset_folder=None, resolutions=None):
       
        if not dataset_folder:
            dataset_folder = self.response.input("Enter dataset folder path: ", "s")
        if not config_folder:
            config_folder = self.response.input("Enter config folder path: ", "s")
        if not id_base:
            id_base = self.response.input("Enter id base: ", "s")
        if not resolutions:
            resolutions = self.response.input("Enter backend resolutions: ", "s")
        
        self.dataset_folder = dataset_folder
        self.config_folder = config_folder
        self.id_base = id_base
        self.resolutions = resolutions

        if not os.path.exists(dataset_folder):            
            self.response.print(f"Dataset folder {dataset_folder} does not exists",'e')
            return False
        if not os.path.exists(config_folder):            
            self.response.print(f"Config folder {config_folder} does not exists",'e')
            return False
        if not id_base:
            self.id_base = "lora"            
            self.response.print(f"Defaulting id base to [blue]lora[/blue]",'e')
        if not resolutions:
            self.resolutions = [512,768,1024]            
            self.response.print(f"Defaulting resolutions to [blue]512,768,1024[/blue]",'e')

        return True
    
        
    def resolve(self):

        default_resolutions = {
            "512" : 5,
            "768" : 4,
            "1024": 3,
            "1536": 1
        }

        default_disabled = {
            "512" : "false",
            "768" : "false",
            "1024": "false",
            "1536": "false"
        }

        self.response.print(f"Testing database folder: [white]{self.dataset_folder}[/white]",'i')

        self.sub_folders = []

        for entry in os.listdir(self.dataset_folder):
            if entry in ['.', '..']:
                continue
            full_path = os.path.join(self.dataset_folder, entry)
            if os.path.isdir(full_path):
                self.subset_mode = 1
                self.sub_folders.append(os.path.basename(full_path))
            
        if self.subset_mode:     
            self.response.print(f"Database folder is a subset folder: {(','.join(self.sub_folders))} ",'i')
        else:
            self.response.print(f"Database folder is a normal folder.",'i')

        self.response.print(f"Creating resolutions: [white]{self.resolutions}[/white]",'i')

        if len(self.sub_folders) > 0:

            for resolution in self.resolutions:
                for folder in self.sub_folders:
                    backend_id = f"{self.id_base}_{folder}_{resolution}"
                    folder = f"{os.path.basename(self.dataset_folder)}/{folder}"
                    self.add_backend_block(backend_id, self.create_block(backend_id, folder, resolution))
                    self.add_backend_block_data(backend_id, "repeats", default_resolutions[str(resolution)])
                    self.add_backend_block_data(backend_id, "disabled", default_disabled[str(resolution)])

                    
            for folder in self.sub_folders:
                embed_id = f"text_embed_{folder}"
                folder = f"{os.path.basename(self.dataset_folder)}/{folder}"
                self.add_backend_block(embed_id, self.get_text_embeds(embed_id, folder))

        else:

            for resolution in self.resolutions:
                backend_id = f"{self.id_base}_{resolution}"
                folder = os.path.basename(self.dataset_folder)
                self.add_backend_block(backend_id, self.create_block(backend_id, folder, resolution))
                self.add_backend_block_data(backend_id, "repeats", default_resolutions[str(resolution)])
                self.add_backend_block_data(backend_id, "disabled", default_disabled[str(resolution)])

            embed_id = f"text_embed_{os.path.basename(self.dataset_folder)}"
            self.add_backend_block(embed_id, self.get_text_embeds(embed_id, folder))
        

    def edit(self, line):

        parts = line.split("=")
        key = parts[0]
        blocks = parts[1].split(",")

        for block in blocks:

            values = block.split(":")

            if len(values) == 2 and self.subset_mode == 1:
                self.response.print(f"Database folder is a subset folder you gave a direct edit","e")
                return 

            if len(values) == 3 and self.subset_mode == 0:
                self.response.print(f"Database folder is a direct folder you gave a subset edit","e")
                return 

            if len(values) == 2:
                resolution = values[0]
                backend_id = f"{self.id_base}_{resolution}"
                self.add_backend_block_data(backend_id, key, values[1])
            
            if len(values) == 3:
                folder = values[0]
                resolution = values[1]
                backend_id = f"{self.id_base}_{folder}_{resolution}"
                self.add_backend_block_data(backend_id, key, values[2])

    def editor(self):

        while True:
            
            line = self.response.input("Enter edit line or [white]q[/white] to quit", "i")
            
            if str(line).strip() == 'q':
                # self.response.console.clear()
                break
            
            self.edit(line)

    def direct_editor(self, backend_file_path, dataset_folder_base):
        
        try:

            backend = None
    
            if backend_file_path:
                with open(backend_file_path, "r", encoding="utf-8") as backend_f:
                    backend = json.load(backend_f)       
    
            for block in backend:
                if not self.id_base:
                    self.id_base = block['id'].split("_")[0]
                if not self.dataset_folder:
                    self.dataset_folder = block["instance_data_dir"].split("/") 
                                      
                self.add_backend_block(block['id'], block)

            if len(self.dataset_folder) == 3:
                self.dataset_folder = f"{dataset_folder_base}/{self.dataset_folder[1]}"
            elif len(self.dataset_folder) == 2:
                self.dataset_folder = f"{dataset_folder_base}/{self.dataset_folder[1]}"

            self.response.print(f"Dataset folder {self.dataset_folder}","i")

            self.sub_folders = []

            for entry in os.listdir(self.dataset_folder):
                if entry in ['.', '..']:
                    continue
                full_path = os.path.join(self.dataset_folder, entry)
                if os.path.isdir(full_path):
                    self.subset_mode = 1
                    self.sub_folders.append(os.path.basename(full_path))
                    
            if self.subset_mode:     
                self.response.print(f"Database folder is a subset folder: {(','.join(self.sub_folders))} ",'i')
            else:
                self.response.print(f"Database folder is a normal folder.",'i')

            while True:

                line = self.response.input("Enter edit line or [white]q[/white] to quit", "i")

                if str(line).strip() == 'q':
                    break

                self.edit(line)

            multidatabackend = []
            for bid, data in self.multidatabackend.items():
                multidatabackend.append(data)                                
            self.response.print(f"Saving backend to {backend_file_path}", 'i')
            with open(f"{backend_file_path}", "w", encoding="utf-8") as f:
                f.write(json.dumps(multidatabackend, indent=4))
                    
                    

        except Exception as e:
            self.response.print(f"Editing failed {e}", 'e')


          
    def save(self):

        multidatabackend = []

        for bid, data in self.multidatabackend.items():
            multidatabackend.append(data)
        
        with open(f"{self.config_folder}/multidatabackend.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(multidatabackend, indent=4))



# "key=prefix:resolution:value"

# "instance_data_dir=shin_20_1:768:datasets//shin_20_1"