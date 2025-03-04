import os
import time
import json
from .response import Response

class UserPromptLibrary:

    def __init__(self):

        self.instance_prompt = None
        self.save_path = None
        self.sample_prompt_file_path = None
        self.response = Response()

        self.upl = {}

    def update_config_data(self, prompts, key, value):

        self.upl = {}

        updated_prompts = {}

        for skey, svalue in prompts.items():
            new_key = skey.replace(f"{{{key}}}", value)
            new_value = svalue.replace(f"{{{key}}}", value)
            updated_prompts[new_key] = new_value

        self.upl.update(updated_prompts)

        self.response.print(f"Updated key {key}: {value}",'s')   
        time.sleep(0.5)

    def take_inputs(self, instance_prompt=None, save_path=None, sample_prompt_file_path=None):
       
        if not instance_prompt:
            instance_prompt = self.response.input("Enter instance prompt: ", "s")
        if not save_path:
            save_path = self.response.input("Enter config folder path: ", "s")
        if not sample_prompt_file_path:
            sample_prompt_file_path = self.response.input("Enter sample prompt file: ", "s")
        
        self.instance_prompt = instance_prompt
        self.save_path = save_path
        self.sample_prompt_file_path = sample_prompt_file_path

        if not os.path.exists(save_path):            
            self.response.print(f"Config folder {save_path} does not exists",'e')
            return False
        if not os.path.exists(sample_prompt_file_path):            
            self.response.print(f"Sample config file {sample_prompt_file_path} does not exists",'e')
            return False

        return True

    def load_files(self):
        
        sample_prompt_file_path = None

        if self.sample_prompt_file_path:
            self.response.print(self.sample_prompt_file_path)
            with open(self.sample_prompt_file_path, "r", encoding="utf-8") as sample_f:
                sample_prompt_file_path = json.load(sample_f)        

        return sample_prompt_file_path
        
    def save(self):

        prompts = self.load_files()
        self.update_config_data(prompts,"--instance_prompt",self.instance_prompt)

        folder = f"{self.save_path}"        
        time.sleep(1)

        os.makedirs(folder, exist_ok=True)
        self.response.print(f"Saving user_prompt_library to {folder}/user_prompt_library.json", 'i')
        with open(f"{folder}/user_prompt_library.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.upl, indent=4))



# upl = UserPromptLibrary()
# verify = upl.take_inputs(
#     instance_prompt="shin",
#     save_path="./config/shin_20_adamw_bf16_constant_1e_4_3000_0",
#     sample_prompt_file_path="./prompts/shin.json"
# )

# if verify:
#     upl.save()