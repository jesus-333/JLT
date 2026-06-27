"""
Training and evaluation loop for the example experiment.

This is the part ``autoresearch`` ultimately cares about : given a configuration and the data loaders, train the model and return the metric to optimise (top-1 accuracy on the validation set).

Every round is bounded twice : it stops after ``num_epochs`` epochs **or** after :data:`MAX_RUNTIME_SECONDS` seconds, whichever comes first. The time budget is checked every batch so a single very long epoch cannot blow past it.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import time

# Specific imports
import torch

# Internal imports
from factories import build_loss, build_optimizer, build_scheduler, set_seed, validate_config
from model import build_model

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Hard wall-clock budget for a single round (10 minutes), as required by the spec.
MAX_RUNTIME_SECONDS = 600

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public function

def train_and_evaluate(config : dict, train_loader, val_loader, num_classes : int) -> float :
    """
    Train the model and return its validation accuracy.

    Parameters
    ----------
    config : dict
        The experiment configuration.
    train_loader : torch.utils.data.DataLoader
        Loader over the training set.
    val_loader : torch.utils.data.DataLoader
        Loader over the validation set.
    num_classes : int
        Number of output classes.

    Returns
    -------
    accuracy : float
        Top-1 accuracy on the validation set, in ``[0, 1]``.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Input checks and setup

    validate_config(config, num_classes)
    set_seed(config["seed"])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Infer the input geometry from an actual batch rather than hard-coding it :
    # this keeps the training loop independent of the data module and lets it be
    # exercised with any loader (e.g. a synthetic one in a smoke test).
    in_channels, in_hw = _infer_input_shape(train_loader)

    model     = build_model(config, in_channels, in_hw, num_classes).to(device)
    optimizer = build_optimizer(config["optimizer"], model.parameters(), config["learning_rate"])
    scheduler = build_scheduler(optimizer, config["use_scheduler"], config["gamma"])
    loss_fn   = build_loss(config["loss_function"], num_classes)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Training loop (bounded by epochs and by wall-clock time)

    start_time   = time.monotonic()
    time_is_up   = False

    for epoch in range(config["num_epochs"]) :

        model.train()

        for images, targets in train_loader :

            # Stop as soon as the time budget is exhausted (checked every batch).
            if time.monotonic() - start_time >= MAX_RUNTIME_SECONDS :
                time_is_up = True
                break

            images  = images.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()
            logits = model(images)
            loss   = loss_fn(logits, targets)
            loss.backward()
            optimizer.step()

        if time_is_up :
            print(f"Stopping early : reached the {MAX_RUNTIME_SECONDS}s time budget during epoch {epoch}.")
            break

        # The scheduler advances once per completed epoch.
        if scheduler is not None :
            scheduler.step()

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Evaluate and return the metric

    return _evaluate_accuracy(model, val_loader, device)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _infer_input_shape(train_loader) -> tuple :
    """
    Infer the input geometry from the first batch of a loader.

    Parameters
    ----------
    train_loader : torch.utils.data.DataLoader
        Loader whose first batch is inspected.

    Returns
    -------
    in_channels : int
        Number of input channels.
    in_hw : tuple
        Spatial size ``(height, width)`` of the input images.

    Raises
    ------
    ValueError
        If the loader is empty (no batch to infer the shape from).
    """

    for images, _ in train_loader :
        return images.shape[1], (images.shape[2], images.shape[3])

    raise ValueError("The training loader is empty : cannot infer the input shape.")

def _evaluate_accuracy(model, val_loader, device) -> float :
    """
    Compute the top-1 accuracy of a model over a data loader.

    Parameters
    ----------
    model : torch.nn.Module
        The trained model.
    val_loader : torch.utils.data.DataLoader
        Loader over the validation set.
    device : torch.device
        Device the model lives on.

    Returns
    -------
    accuracy : float
        The fraction of correctly classified samples, in ``[0, 1]`` (``0.0`` if the loader is empty).
    """

    model.eval()

    correct = 0
    total   = 0

    with torch.no_grad() :
        for images, targets in val_loader :
            images  = images.to(device)
            targets = targets.to(device)

            predictions = model(images).argmax(dim = 1)
            correct    += int((predictions == targets).sum().item())
            total      += int(targets.shape[0])

    # Guard against an empty validation set rather than dividing by zero.
    if total == 0 :
        return 0.0

    return correct / total
