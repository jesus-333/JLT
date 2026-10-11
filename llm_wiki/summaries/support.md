# Support Tool Summary

## Purpose

The `support` tool contains small command-line utilities that assist with LLM and model-related workflows. Its implementation lives under `src/jlt/support/` and is exposed through the shared `jlt` entry point.

## Hugging Face metadata download

The `get-hf-metadata` subcommand downloads safetensors metadata for a model hosted on Hugging Face and writes the model's tensor names, data types, and shapes to a text file.

```bash
jlt support get-hf-metadata --model Qwen/Qwen3.8-27B
```

The model identifier is mandatory and must use the standard `user/model` format.

### Options

- `--model` — mandatory Hugging Face model identifier in `user/model` format.
- `--output_file` — optional output path. If omitted, the command writes `{model_name}_metadata.txt` in the current directory. For example, `Qwen/Qwen3.8-27B` produces `Qwen3.8-27B_metadata.txt`.
- `--print` — optionally prints the downloaded metadata to the console in addition to writing it to the output file.

Example with all options:

```bash
jlt support get-hf-metadata \
    --model Qwen/Qwen3.8-27B \
    --output_file ./qwen_metadata.txt \
    --print
```

Each output line has the following human-readable structure:

```text
<tensor name>  <data type>  <shape>
```

Files and tensor names are sorted before writing, making the output deterministic. The command retrieves metadata through `huggingface_hub.get_safetensors_metadata`; it does not download the model weights.

If the model identifier is invalid, Hugging Face cannot retrieve the metadata, the model has no tensor metadata, or the destination cannot be written, the command prints an error and returns exit code `1`. On success, it reports the resolved output path and returns `0`.

## Source layout

```text
src/jlt/support/
    __init__.py
    cli.py                    # CLI registration and command entry point
    huggingface_metadata.py   # Validation, download, formatting, and file writing
```

The tool is registered in the top-level `TOOLS` tuple in `src/jlt/cli.py`. The required `huggingface-hub` package is a core project dependency declared in `pyproject.toml`.
