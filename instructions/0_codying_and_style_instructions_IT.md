Qui ci sono alcune indicazioni che voglio che segui mentre scrivi codice

# Divisori

Se devi dividere blocchi di codice usa la seguente stringa
```python
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
```

E.g. se devi dividere gli imports dalle dichirazione delle funzioni

Se ti trovi all'interno di una funzione invece usa la seguente stringa (ovviamente rispettando l'indentatura)
```python
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
```

Cerca sempre di dividere ogni file lungo in sezioni tematiche  (e.g. imports, funzioni principali, funzioni secondarie etc).
Se hai funzione lunghe vale lo stesso. Dividile in blocchi tematici (e.g. check degli input, preprocess, calcoli effettivi, check output).
Funzioni molto lunghe è meglio se vengono suddivise in sottofunzioni specifiche.

# Note di stile

- Usa sempre lo snacke case, (anche per le classi).
- I nome delle variabili devono essere esplicativi (anche se sono lunghi va bene, basta che sia molto chiaro per cosa è usata)
- Metti sempre spazi intorno agli uguali, sia per operazioni tra variabili che quando passi argoment a delle funzioni. 
    - E.g. (1) : `a=1+2` ---> `a = 1 + 2`
    - E.g. (2) : `function(a=2)` --> `function(a = 2)`
- Se specifichi il tipo di variabile in input o ritornato da una funzione metti sempre lo spazio prima dei due punti
    - E.g. : `def funct(a: int) --> int:` --> `def funct(a : int) --> int :` 
- Discorso simile per gli `if`. Lascia uno spazio tra la condizione e `:` 
    - E.g. : `if condition:` --> `if condition :`
- Commenta il più possibile il codice all'interno delle funzioni.
- Allinea quando possibili gli uguali
    - E.g. se dichiari un dizionario con molte variabili allinea tutti gli uguali per ogni argomento del dizionario
    - E.g. se usi una funzioni e scrivi la call in più linee, nel caso chiami solo un argomento per linea allinea gli uguali
- Quando usi `argparse` metti una descrizione esaustiva per ogni argomento, il tipo di input, e nel caso sia opzionale un valore di default

# Docstring

- Per le docstring usa sempre il numpydoc come formato
- In futurò usero `sphynx` per automatizzare la creazione della documentazione. Se nelle docstring fai riferimento ad altri moduli/classi/funzioni usa la sintassi di sphynx che permetta di creare gli hyperlink. Inoltre per link lunghi usa la `~` che abbrevia gli hyperlink solo alla sua ultima parte
- Anche se fai una docstring docstring di una sola riga di testo vai sempre a capo (vedi esempio in fondo a questa sezione).

## Short docstring example
```python
""" This is a WRONG short docstring """
```

```python
""" 
This is a RIGHT short Docstring
"""
```

# Esempio

Qui di seguito troverai un esempio concreto.

Questo è un blocco di codice come lo hai scritto inizialmente tu. 
```python
"""Command line entry point for Jesus's LLM Tools (JLT).

JLT is a collection of LLM-powered tools. Every tool is invoked through the
single ``jlt`` command using the syntax::

    jlt <tool_name> <tool_subcommand, tool variable, tool flags>

Each tool lives in its own subpackage under ``jlt`` and exposes a
``register(subparsers)`` function in its ``cli`` module. That function attaches
the tool's own argument parser (with its subcommands, variables and flags) to
the shared top-level parser, keeping every tool self-contained.
"""

from __future__ import annotations

import argparse
from importlib import import_module

from . import __version__

# Each entry maps a tool name to the module that exposes ``register(subparsers)``.
# Adding a new tool is a one-line change here.
TOOLS = (
    "jlt.autoresearch.cli",
    "jlt.club.cli",
)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level ``jlt`` parser and let every tool register itself."""
    parser = argparse.ArgumentParser(
        prog="jlt",
        description="Jesus's LLM Tools (JLT): a collection of LLM-powered tools.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="tool",
        metavar="<tool_name>",
        help="The JLT tool to run.",
    )
    subparsers.required = True

    for module_path in TOOLS:
        module = import_module(module_path)
        module.register(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and dispatch to the selected tool.

    Returns the tool's exit code (defaults to ``0``).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    # ``func`` is set by each tool via ``set_defaults`` in its ``register``.
    return args.func(args) or 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
```

Con le mie regole di stile deve diventerebbe 
```python
"""
Command line entry point for Jesus's LLM Tools (JLT).

JLT is a collection of LLM-powered tools. Every tool is invoked through the
single ``jlt`` command using the syntax::

    jlt <tool_name> <tool_subcommand, tool variable, tool flags>

Each tool lives in its own subpackage under ``jlt`` and exposes a
``register(subparsers)`` function in its ``cli`` module. That function attaches
the tool's own argument parser (with its subcommands, variables and flags) to
the shared top-level parser, keeping every tool self-contained.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports sectio

from __future__ import annotations

# Full module imports
import argparse

# Specific imports
from importlib import import_module

# Internal imports
from . import __version__

# Each entry maps a tool name to the module that exposes ``register(subparsers)``.
# Adding a new tool is a one-line change here.
TOOLS = (
    "jlt.autoresearch.cli",
    "jlt.club.cli",
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Support function

def build_parser() -> argparse.ArgumentParser :
    """
    Build the top-level ``jlt`` parser and let every tool register itself.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Build jlt parser

    parser = argparse.ArgumentParser(
        prog        = "jlt",
        description = "Jesus's LLM Tools (JLT): a collection of LLM-powered tools.",
    )

    parser.add_argument(
        "--version",
        action  = "version",
        version = f"%(prog)s {__version__}",
    )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Build tool's parser

    subparsers = parser.add_subparsers(
        dest    = "tool",
        metavar = "<tool_name>",
        help    = "The JLT tool to run.",
    )
    subparsers.required = True

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    for module_path in TOOLS:
        module = import_module(module_path)
        module.register(subparsers)

    return parser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Main function

def main(argv : list[str] | None = None) -> int :
    """
    Parse ``argv`` and dispatch to the selected tool.

    Returns the tool's exit code (defaults to ``0``).
    """
    
    # Get input argument
    parser  = build_parser()
    args    = parser.parse_args(argv)

    # Note that ``func`` is set by each tool via ``set_defaults`` in its ``register``.
    return args.func(args) or 0

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

```
