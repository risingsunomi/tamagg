import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
import numpy as np
import warnings
from pathlib import Path
from accelerate import disk_offload

"""
This needs a lot of VRAM. Current PC not able to run it.
"""

class DolphinVisionModel:
    """
    Dolphin Vision Model class
    Using the cognitivecomputations/dolphin-vision-72b local vision model for image descriptions
    """
    def __init__(self, model_name='cognitivecomputations/dolphin-vision-72b', device='cuda'):
        # disable some warnings
        transformers.logging.set_verbosity_error()
        transformers.logging.disable_progress_bar()
        warnings.filterwarnings('ignore')

        # set device
        torch.set_default_device(device)  # 'cuda' or 'cpu'

        # create model and tokenizer
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map='auto',
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            offload_folder=Path("./data/dolphin_offload"),
            offload_state_dict=True
        ).eval()
        
        # disk_offload(model=self.model, offload_dir=Path("./data/disk_offload"))

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )

    def describe_image(self, image_input: any, prompt: str='Describe this image in detail'):
        """
        describe_image

        Describe an image via the prompt and image input
        """
        # text prompt
        messages = [
            {"role": "user", "content": f'<image>\n{prompt}'}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        text_chunks = [self.tokenizer(chunk).input_ids for chunk in text.split('<image>')]
        input_ids = torch.tensor(text_chunks[0] + [-200] + text_chunks[1], dtype=torch.long).unsqueeze(0)

        # process image input
        if isinstance(image_input, Path):
            image = Image.open(image_input)
        elif isinstance(image_input, np.ndarray):
            image = Image.fromarray(image_input)
        else:
            raise ValueError("Unsupported image input type. Provide a file path or a numpy array.")

        image_tensor = self.model.process_images([image], self.model.config).to(dtype=self.model.dtype)

        # generate
        output_ids = self.model.generate(
            input_ids,
            images=image_tensor,
            max_new_tokens=2048,
            use_cache=True
        )[0]

        return self.tokenizer.decode(output_ids[input_ids.shape[1]:], skip_special_tokens=True).strip()
