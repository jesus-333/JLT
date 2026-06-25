"""
Backend subpackage : a unified interface to several LLM providers.

The backend code is placed inside ``shared_knowledge`` because it is meant to be
reused by every JLT tool. Each provider lives in its own module and subclasses
:class:`~jlt.shared_knowledge.backend.generic.generic_backend`.

The most useful entry points are re-exported here for convenience :

- :class:`~jlt.shared_knowledge.backend.generic.generic_backend` : the abstract
  template every backend inherits from.
- :func:`~jlt.shared_knowledge.backend.registry.load_backend` : instantiate the
  active (or a named) backend, ready to be used by a tool.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Re-exports

from .generic import generic_backend
from .registry import (
    BACKEND_CLASSES,
    configure_backend,
    list_backends,
    load_backend,
    remove_backend,
    set_active_backend,
    get_active_backend_name,
)

__all__ = [
    "generic_backend",
    "BACKEND_CLASSES",
    "configure_backend",
    "list_backends",
    "load_backend",
    "remove_backend",
    "set_active_backend",
    "get_active_backend_name",
]
