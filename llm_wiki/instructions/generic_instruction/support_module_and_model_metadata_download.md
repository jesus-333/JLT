Add a small function to the cli. This function has the purpose to download model information/metadata from huggingface.
Name of the function is `get-hf-metadata`.

Take inspiration from this snippet
```python
from huggingface_hub import get_safetensors_metadata

model = "..."

meta = get_safetensors_metadata(model)
for fname, fmeta in meta.files_metadata.items():
    for name, t in sorted(fmeta.tensors.items()):
        print(f"{name:75s} {t.dtype:6s} {t.shape}")
```

Basically, read the model metadata and get the layers name and shape. But instead of printing them, save them in a file.
The `url` should be in the classic hugging face format, i.e. `user/model`. E.g. for qwen3.8 27b `Qwen/Qwen3.8-27B`.

The cli function should have the following flag
- `--model`. MANDATORY
- `--output_file`. OPTIONAL. Specify the path and name of the final file. If not specified must default to `{model_name}_metadata.txt` in the current directory, where `{model_name}` is the effective name of the model (e.g. `Qwen3.8-27B` for `Qwen/Qwen3.8-27B`).
- `--print`. OPTIONAL. If added it should also print the information downloaded on the console.

Regarding the code/package general structure. Create a new tool called `support`
Its specific purpose will be to house small CLI support functions like this one.
So the final command should be something like `jlt support get-hf-metadata` and then all the flags.
