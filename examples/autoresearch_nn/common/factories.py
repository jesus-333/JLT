"""
Factories and configuration validation for the example neural-network experiment.

This module turns the plain strings / numbers found in the experiment configuration into the corresponding PyTorch objects (activation, optimizer, loss, scheduler) and validates that the configuration is internally consistent before anything is built.

Keeping every "string -> object" mapping here (instead of scattering ``if name == ...`` checks across the model and the training loop) keeps the rest of the code short and gives a single place to extend when a new activation / optimizer / loss is added.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import random

# Specific imports
import numpy as np
import torch
from torch import nn, optim

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# The activation functions accepted by ``activation_function`` in the config.
ACTIVATIONS = {
    "relu"       : nn.ReLU,
    "tanh"       : nn.Tanh,
    "sigmoid"    : nn.Sigmoid,
    "leaky_relu" : nn.LeakyReLU,
    "elu"        : nn.ELU,
    "selu"       : nn.SELU,
    "gelu"       : nn.GELU,
}

# The optimizers accepted by ``optimizer`` in the config.
OPTIMIZERS = {
    "sgd"      : optim.SGD,
    "adam"     : optim.Adam,
    "rmsprop"  : optim.RMSprop,
    "adagrad"  : optim.Adagrad,
    "adadelta" : optim.Adadelta,
    "adamax"   : optim.Adamax,
    "nadam"    : optim.NAdam,
}

# The loss functions accepted by ``loss_function`` in the config.
LOSSES = (
    "cross_entropy", "mse", "mae", "huber", "kldiv", "nll", "bce", "bce_with_logits",
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Configuration validation

def validate_config(config : dict, num_classes : int) -> None :
    """
    Check that an experiment configuration is internally consistent.

    Following the repository convention, any inconsistency raises an exception rather than being silently fixed : better safe than sorry.

    Parameters
    ----------
    config : dict
        The experiment configuration dictionary.
    num_classes : int
        The number of output classes (derived from the data), used to sanity-check the model output.

    Raises
    ------
    KeyError
        If a mandatory key is missing.
    ValueError
        If a value is out of range, an enum value is unknown, or a list length does not match its declared count.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Mandatory keys

    mandatory_keys = (
        "use_cnn_backbone", "n_cnn_layer", "cnn_layer_size", "pool_layer_size",
        "n_fc_layer", "dropout_2d_rate", "batch_norm_cnn", "fc_layer_size",
        "activation_function", "dropout_rate", "batch_norm_fc", "learning_rate",
        "optimizer", "batch_size", "num_epochs", "loss_function", "use_scheduler",
        "gamma", "seed",
    )

    for key in mandatory_keys :
        if key not in config :
            raise KeyError(f"Missing mandatory configuration key : '{key}'.")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # CNN backbone consistency

    # The per-layer lists must match the declared number of layers, but only when
    # the backbone is actually used.
    if config["use_cnn_backbone"] :
        n_cnn = config["n_cnn_layer"]
        if len(config["cnn_layer_size"]) != n_cnn :
            raise ValueError(
                f"'cnn_layer_size' must have 'n_cnn_layer' ({n_cnn}) entries, "
                f"got {len(config['cnn_layer_size'])}."
            )
        if len(config["pool_layer_size"]) != n_cnn :
            raise ValueError(
                f"'pool_layer_size' must have 'n_cnn_layer' ({n_cnn}) entries, "
                f"got {len(config['pool_layer_size'])}."
            )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # FC head consistency

    if len(config["fc_layer_size"]) != config["n_fc_layer"] :
        raise ValueError(
            f"'fc_layer_size' must have 'n_fc_layer' ({config['n_fc_layer']}) entries, "
            f"got {len(config['fc_layer_size'])}."
        )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Ranges and enums

    for rate_key in ("dropout_2d_rate", "dropout_rate") :
        rate = config[rate_key]
        if not (0.0 <= rate < 1.0) :
            raise ValueError(f"'{rate_key}' must be in [0, 1), got {rate}.")

    if config["learning_rate"] <= 0.0 :
        raise ValueError(f"'learning_rate' must be positive, got {config['learning_rate']}.")

    if config["batch_size"] <= 0 :
        raise ValueError(f"'batch_size' must be positive, got {config['batch_size']}.")

    if config["num_epochs"] <= 0 :
        raise ValueError(f"'num_epochs' must be positive, got {config['num_epochs']}.")

    if config["activation_function"] not in ACTIVATIONS :
        raise ValueError(
            f"Unknown 'activation_function' : '{config['activation_function']}'. "
            f"Expected one of {sorted(ACTIVATIONS)}."
        )

    if config["optimizer"] not in OPTIMIZERS :
        raise ValueError(
            f"Unknown 'optimizer' : '{config['optimizer']}'. Expected one of {sorted(OPTIMIZERS)}."
        )

    if config["loss_function"] not in LOSSES :
        raise ValueError(
            f"Unknown 'loss_function' : '{config['loss_function']}'. Expected one of {sorted(LOSSES)}."
        )

    if num_classes < 2 :
        raise ValueError(f"'num_classes' must be at least 2, got {num_classes}.")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Builders

def build_activation(name : str) -> nn.Module :
    """
    Return a fresh activation module for the given name.

    Parameters
    ----------
    name : str
        One of the keys of :data:`ACTIVATIONS`.

    Returns
    -------
    activation : torch.nn.Module
        A new activation module.
    """

    return ACTIVATIONS[name]()

def build_optimizer(name : str, parameters, learning_rate : float) -> optim.Optimizer :
    """
    Return an optimizer for the given name, parameters and learning rate.

    Parameters
    ----------
    name : str
        One of the keys of :data:`OPTIMIZERS`.
    parameters : iterable
        The model parameters to optimise.
    learning_rate : float
        The learning rate.

    Returns
    -------
    optimizer : torch.optim.Optimizer
        The configured optimizer.
    """

    return OPTIMIZERS[name](parameters, lr = learning_rate)

def build_scheduler(optimizer : optim.Optimizer, use_scheduler : bool, gamma : float) :
    """
    Return an exponential learning-rate scheduler, or ``None`` if disabled.

    Parameters
    ----------
    optimizer : torch.optim.Optimizer
        The optimizer to attach the scheduler to.
    use_scheduler : bool
        Whether a scheduler should be used at all.
    gamma : float
        The multiplicative decay applied to the learning rate every epoch.

    Returns
    -------
    scheduler : torch.optim.lr_scheduler.ExponentialLR or None
        The scheduler, or ``None`` when ``use_scheduler`` is ``False``.
    """

    if not use_scheduler :
        return None

    return optim.lr_scheduler.ExponentialLR(optimizer, gamma = gamma)

def build_loss(name : str, num_classes : int) :
    """
    Return a loss callable ``loss_fn(logits, targets)`` for the given name.

    The model always produces raw logits of shape ``(batch, num_classes)`` and the targets are integer class indices.
    Classification losses (``cross_entropy``, ``nll``) consume those directly ; the regression / distribution losses (``mse``, ``mae``, ``huber``, ``kldiv``, ``bce``, ``bce_with_logits``) are wrapped so they receive a sensible transform of the logits and a one-hot version of the targets.
    They are supported mostly for completeness : ``cross_entropy`` is the natural choice for this multi-class problem.

    Parameters
    ----------
    name : str
        One of :data:`LOSSES`.
    num_classes : int
        Number of classes, needed to build one-hot targets for the non-classification losses.

    Returns
    -------
    loss_fn : callable
        A function mapping ``(logits, targets)`` to a scalar loss tensor.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Native classification losses

    if name == "cross_entropy" :
        cross_entropy = nn.CrossEntropyLoss()
        return lambda logits, targets : cross_entropy(logits, targets)

    if name == "nll" :
        # ``NLLLoss`` expects log-probabilities, so apply ``log_softmax`` first.
        nll = nn.NLLLoss()
        return lambda logits, targets : nll(torch.log_softmax(logits, dim = 1), targets)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Losses needing a one-hot target

    # Helper turning integer targets into a float one-hot matrix matching the logits.
    def _one_hot(targets) :
        return torch.nn.functional.one_hot(targets, num_classes = num_classes).float()

    if name == "kldiv" :
        # ``KLDivLoss`` expects log-probabilities as input and probabilities as target.
        kldiv = nn.KLDivLoss(reduction = "batchmean")
        return lambda logits, targets : kldiv(torch.log_softmax(logits, dim = 1), _one_hot(targets))

    if name == "bce_with_logits" :
        bce_logits = nn.BCEWithLogitsLoss()
        return lambda logits, targets : bce_logits(logits, _one_hot(targets))

    if name == "bce" :
        bce = nn.BCELoss()
        return lambda logits, targets : bce(torch.sigmoid(logits), _one_hot(targets))

    # The plain regression losses compare the predicted class probabilities to the one-hot target.
    regression_losses = {
        "mse"   : nn.MSELoss(),
        "mae"   : nn.L1Loss(),
        "huber" : nn.HuberLoss(),
    }
    regression_loss = regression_losses[name]
    return lambda logits, targets : regression_loss(torch.softmax(logits, dim = 1), _one_hot(targets))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Reproducibility

def set_seed(seed : int) -> None :
    """
    Seed every relevant random number generator for reproducibility.

    Parameters
    ----------
    seed : int
        The random seed to apply to ``random``, ``numpy`` and ``torch``.
    """

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    # Make cuDNN deterministic too, so a re-run with the same seed is reproducible.
    if torch.cuda.is_available() :
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark     = False
