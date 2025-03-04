import os
import time
import json
from .response import Response
from collections.abc import Mapping, Sequence

class ScientificNotationEncoder(json.JSONEncoder):

    def encode(self, o):        
        if isinstance(o, Mapping):
            result = "{\n"
            for k, v in o.items():
                if k == "--learning_rate":
                    encoded_value = self._format_value(v)
                else:
                    encoded_value = self.encode(v)                
                result += f'  "{k}": {encoded_value},\n'
            result = result.rstrip(",\n") + "\n}"
            return result
        elif isinstance(o, Sequence) and not isinstance(o, str):
            return "[\n" + ",\n".join("  " + self.encode(i) for i in o) + "\n]"        
        return json.dumps(o, ensure_ascii=False)

    def _format_value(self, o):
        formatted = "{:e}".format(o)
        base, exponent = formatted.split("e")
        base = base.rstrip("0").rstrip(".") if "." in base else base
        exponent = exponent.replace("+0", "+").replace("-0", "-").lstrip("+")
        return f"{base}e{exponent}"   

def format_float(o):

    if isinstance(o, float):
        formatted = "{:e}".format(o)
        base, exponent = formatted.split("e")
        base = base.rstrip("0").rstrip(".") if "." in base else base
        exponent = exponent.replace("+0", "+").replace("-0", "-").lstrip("+")
        return f"{base}e{exponent}"        
    else:
        return o

class Config:

    def __init__(self):

        self.instance_prompt = None
        self.dataset_folder = None
        self.config_folder = None
        self.output_folder = None
        self.namig_preset_file_path = None
        self.instance_prompt_version = None
        self.skip_editor = 0

        self.options_file = None
        self.sample_config_file_path = None
        self.response = Response()

        self.config = {}

    def add_config_data(self, key, value):

        self.config[key] = value
        self.response.print(f"Updated key {key}: {value}",'s')   
        time.sleep(0.5)

    def remove_config_data(self, key):    

        if key in self.config:
            del self.config[key]
            self.response.print(f"Deleted key: {key}",'s')   

    def take_inputs(self, instance_prompt=None, instance_prompt_version=None, config_folder=None, output_folder=None, dataset_folder=None, sample_config_file_path=None, options_file=None, naming_preset_file=None):
       
        if not instance_prompt:
            instance_prompt = self.response.input("Enter instance prompt: ", "s")
        if not instance_prompt_version:
            instance_prompt_version = self.response.input("Enter instance prompt version: ", "s")
        if not dataset_folder:
            dataset_folder = self.response.input("Enter dataset folder path: ", "s")
        if not config_folder:
            config_folder = self.response.input("Enter config folder path: ", "s")
        if not output_folder:
            output_folder = self.response.input("Enter output folder path: ", "s")
        if not sample_config_file_path:
            sample_config_file_path = self.response.input("Enter config sample file: ", "s")
        if not options_file:
            options_file = self.response.input("Enter config options file: ", "s")
        if not naming_preset_file:
            naming_preset_file = self.response.input("Enter naming preset file: ", "s")
        
        self.instance_prompt = instance_prompt
        self.instance_prompt_version = instance_prompt_version
        self.dataset_folder = dataset_folder
        self.config_folder = config_folder
        self.output_folder = output_folder
        self.sample_config_file_path = sample_config_file_path
        self.options_file = options_file
        self.namig_preset_file_path = naming_preset_file

        if not os.path.exists(dataset_folder):            
            self.response.print(f"Dataset folder {dataset_folder} does not exists",'e')
            return False
        if not os.path.exists(config_folder):            
            self.response.print(f"Config folder {config_folder} does not exists",'e')
            return False
        if not os.path.exists(output_folder):            
            self.response.print(f"Config output folder {output_folder} does not exists",'e')
            return False
        if not os.path.exists(sample_config_file_path):            
            self.response.print(f"Sample config file {sample_config_file_path} does not exists",'e')
            return False
        if not os.path.exists(options_file):            
            self.options_file = None
            self.response.print(f"Config options file {options_file} does not exists",'e')
        if not os.path.exists(naming_preset_file):            
            self.namig_preset_file_path = None
            self.response.print(f"Config naming preset file {naming_preset_file} does not exists",'e')

        self.add_config_data("--instance_prompt", self.instance_prompt)
        self.add_config_data("--tracker_project_name", self.instance_prompt)

        return True

    def load_files(self):
        
        sample_config_file_path = None
        naming_preset_file = None
        options = None

        if self.sample_config_file_path:
            with open(self.sample_config_file_path, "r", encoding="utf-8") as sample_f:
                sample_config_file_path = json.load(sample_f)        

        if self.options_file:
            with open(self.options_file, "r", encoding="utf-8") as options_f:
                options = json.load(options_f)        
        
        if self.namig_preset_file_path:
            with open(self.namig_preset_file_path, "r", encoding="utf-8") as naming_f:
                naming_preset_file = json.load(naming_f)        

        return sample_config_file_path, options, naming_preset_file

    def editor(self):

        if self.skip_editor == 1:
            return

        while True:

            config, options, naming = self.load_files()
            config.update(self.config)
            filtered = []

            config_keys = list(config.keys())

            if options:
                filtered = [k for k in config_keys if (k in options) or not options]

            rows = []
    
            picked = config_keys
            if options:
                picked = filtered

            for i, k in enumerate(filtered, start=1):
                if k == '--learning_rate':
                    rows.append([str(i), k, format_float(config[k])])
                else:
                    rows.append([str(i), k, str(config[k])])
                                    
            self.response.edit_table("Config editor", ['index','key','value'], rows)
            index = self.response.input("Enter index to edit or [white]q[/white] to quit", "i")
            
            if str(index).strip() == 'q':
                # self.response.console.clear()
                break
            
            index = int(index) - 1

            if picked[index]:
                
                self.response.print(f"Editing {picked[index]}:", 'i')
                value = self.response.input("Enter value", "s")
                self.add_config_data(picked[index], value)

                auto_divides = [
                    "--max_train_steps",
                    "--checkpointing_steps",
                    "--checkpoints_total_limit",
                    "--lr_warmup_steps",
                ]

                if(picked[index] == "--train_batch_size"):
                    for auto_divide in auto_divides:

                        auto_value = int(config[auto_divide]) / int(value)
                        if auto_divide in self.config:
                            auto_value = int(self.config[auto_divide]) / int(value)

                        self.add_config_data(auto_divide, int(auto_value))

            else:
                self.response.print(f"Editing failed", 'e')

            time.sleep(1)

        time.sleep(1)

    def apply_name_preset(self, config, keys):

        folder_name_with_instance_and_version = f"{self.instance_prompt}_{self.instance_prompt_version}"
        folder_name_with_only_version = f"{self.instance_prompt_version}"

        for key in keys:
            value = str(format_float(config[key])).replace('-','_')
            folder_name_with_instance_and_version = f"{folder_name_with_instance_and_version}_{str(value)}"
            folder_name_with_only_version = f"{folder_name_with_only_version}_{str(value)}"
            
        self.response.print(f"Folder name: {folder_name_with_instance_and_version}")
        self.response.print(f"Output Folder name: {folder_name_with_only_version}")

        self.add_config_data("--tracker_run_name",folder_name_with_instance_and_version)
        self.add_config_data("--user_prompt_library",f"{self.config_folder}/{folder_name_with_instance_and_version}/user_prompt_library.json")
        self.add_config_data("--data_backend_config",f"{self.config_folder}/{folder_name_with_instance_and_version}/multidatabackend.json")
        self.add_config_data("--output_dir",f"{self.output_folder}/{self.instance_prompt}/{folder_name_with_only_version}")

        return folder_name_with_instance_and_version, folder_name_with_only_version
        
    def save(self):

        config, options, naming = self.load_files()
        config.update(self.config)
        folder = f"{self.config_folder}/{self.instance_prompt}"
        
        if naming:
            folder_i, folder_v = self.apply_name_preset(config=config,keys=naming)
            config.update(self.config)
            folder = f"{self.config_folder}/{folder_i}"

        time.sleep(1)

        os.makedirs(folder, exist_ok=True)
        self.response.print(f"Saving config to {folder}/config.json", 'i')
        with open(f"{folder}/config.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(config, indent=4, cls=ScientificNotationEncoder))

        return folder



