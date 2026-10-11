"""
Download and format model tensor metadata from Hugging Face.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import pathlib

# Specific imports
from huggingface_hub import get_safetensors_metadata

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Metadata functions

def get_default_output_path(model : str) -> pathlib.Path :
    """
    Return the default output path for a Hugging Face model.

    Parameters
    ----------
    model : str
        Hugging Face model identifier in ``user/model`` format.

    Returns
    -------
    output_path : pathlib.Path
        Path named after the model in the current working directory.
    """

    model_name = _validate_model_identifier(model)
    return pathlib.Path.cwd() / f"{model_name}_metadata.txt"

def download_metadata(model : str, output_file : str | pathlib.Path | None = None) -> tuple[pathlib.Path, str] :
    """
    Download a model's safetensors metadata and save its tensor information.

    Parameters
    ----------
    model : str
        Hugging Face model identifier in ``user/model`` format.
    output_file : str or pathlib.Path, optional
        Destination file. If omitted, ``{model_name}_metadata.txt`` is written
        in the current working directory.

    Returns
    -------
    output_path : pathlib.Path
        Absolute path of the metadata file that was written.
    formatted_metadata : str
        Text written to the output file.
    """

    # Validate the model identifier before making a network request.
    _validate_model_identifier(model)

    if output_file is None :
        output_path = get_default_output_path(model)
    else :
        output_path = pathlib.Path(output_file).expanduser().resolve()

    # Download only the safetensors index and headers, not the model weights.
    metadata           = get_safetensors_metadata(model)
    formatted_metadata = _format_metadata(metadata)

    # Do not silently create a mistyped destination directory.
    output_path.write_text(formatted_metadata, encoding = "utf-8")

    return output_path, formatted_metadata

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Internal helpers

def _validate_model_identifier(model : str) -> str :
    """
    Validate a model identifier and return its effective model name.
    """

    if not isinstance(model, str) or model.strip() != model :
        raise ValueError("The model must be a non-empty string without leading or trailing whitespace.")

    model_parts = model.split("/")
    if len(model_parts) != 2 or not all(model_parts) :
        raise ValueError("The model must use the Hugging Face 'user/model' format.")

    return model_parts[1]

def _format_metadata(metadata : object) -> str :
    """
    Format safetensors metadata as one human-readable line per tensor.
    """

    lines = []

    # Sort files and tensors so repeated downloads produce stable output.
    for file_name in sorted(metadata.files_metadata) :
        file_metadata = metadata.files_metadata[file_name]
        for tensor_name, tensor_metadata in sorted(file_metadata.tensors.items()) :
            lines.append(
                f"{tensor_name:75s} {str(tensor_metadata.dtype):6s} {tensor_metadata.shape}"
            )

    if not lines :
        raise ValueError("No tensor metadata was found for the model.")

    return "\n".join(lines) + "\n"
