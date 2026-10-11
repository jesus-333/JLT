"""
CLI wiring for small JLT support utilities.

Invoked as::

    jlt support <subcommand, flags>
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import argparse

# Internal imports
from . import huggingface_metadata

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Registration function

def register(subparsers : argparse._SubParsersAction) -> argparse.ArgumentParser :
    """
    Attach the ``support`` parser to the top-level ``jlt`` parser.
    """

    parser = subparsers.add_parser(
        "support",
        help        = "Run small support utilities.",
        description = "Run small support utilities.",
    )
    parser.set_defaults(func = lambda args : parser.print_help())

    support_subparsers = parser.add_subparsers(
        dest    = "support_command",
        metavar = "<subcommand>",
        help    = "The support operation to run.",
    )

    metadata_parser = support_subparsers.add_parser(
        "get-hf-metadata",
        help        = "Download model tensor metadata from Hugging Face.",
        description = "Download layer names, data types, and shapes from a Hugging Face safetensors model.",
    )
    metadata_parser.add_argument(
        "--model",
        type     = str,
        required = True,
        help     = "Hugging Face model identifier in 'user/model' format (mandatory).",
    )
    metadata_parser.add_argument(
        "--output_file",
        type     = str,
        required = False,
        default  = None,
        help     = "Output file path. Optional; defaults to '{model_name}_metadata.txt' in the current directory.",
    )
    metadata_parser.add_argument(
        "--print",
        action   = "store_true",
        dest     = "print_metadata",
        default  = False,
        help     = "Also print the downloaded metadata to the console. Optional; defaults to false.",
    )
    metadata_parser.set_defaults(func = run_get_hf_metadata)

    return parser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Subcommand entry point

def run_get_hf_metadata(args : argparse.Namespace) -> int :
    """
    Download and save Hugging Face model tensor metadata.
    """

    try :
        output_path, formatted_metadata = huggingface_metadata.download_metadata(
            model       = args.model,
            output_file = args.output_file,
        )
    except Exception as error :
        print(f"Error while downloading metadata for model '{args.model}' : {error}")
        return 1

    if args.print_metadata :
        print(formatted_metadata, end = "")

    print(f"Metadata for model '{args.model}' saved successfully to '{output_path}'.")
    return 0
