"""
Configurable neural-network model for the example experiment.

The model is built entirely from the experiment configuration : an optional convolutional backbone followed by a fully-connected head ending in one logit per class.
Every architectural choice (number of layers, layer sizes, dropout, batch-norm, activation) comes from the config, which is exactly what the ``autoresearch`` optimisation loop tweaks between rounds.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Specific imports
import torch
from torch import nn

# Internal imports
from factories import build_activation

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Convolutions keep the spatial size (kernel 3, padding 1) ; only the pooling
# layers shrink it. Kept as constants so the spatial arithmetic is explicit.
CONV_KERNEL_SIZE = 3
CONV_PADDING     = 1

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Model definition

class configurable_net(nn.Module) :
    """
    A CNN-backbone + fully-connected classifier built from a configuration.

    Parameters
    ----------
    config : dict
        The experiment configuration (see the experiment description for the keys).
    in_channels : int
        Number of channels of the input images.
    in_hw : tuple
        Spatial size ``(height, width)`` of the input images.
    num_classes : int
        Number of output classes.
    """

    def __init__(self, config : dict, in_channels : int, in_hw : tuple, num_classes : int) -> None :
        """
        Build the backbone and the head from the configuration.
        """

        super().__init__()

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Optional convolutional backbone

        self.backbone = _build_backbone(config, in_channels)

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Work out the flattened feature size with a dummy forward

        # Rather than computing the post-pooling spatial size by hand (error prone
        # with arbitrary pooling), push a zero tensor through the backbone once and
        # read the resulting number of features. An over-aggressive pooling that
        # collapses the spatial dimensions surfaces here as a clear runtime error.
        with torch.no_grad() :
            dummy           = torch.zeros(1, in_channels, in_hw[0], in_hw[1])
            flattened_size  = self.backbone(dummy).flatten(1).shape[1]

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Fully-connected head

        self.head = _build_head(config, flattened_size, num_classes)

    def forward(self, x : torch.Tensor) -> torch.Tensor :
        """
        Run the input through the backbone and the head.

        Parameters
        ----------
        x : torch.Tensor
            Input batch of shape ``(batch, channels, height, width)``.

        Returns
        -------
        logits : torch.Tensor
            Raw class scores of shape ``(batch, num_classes)``.
        """

        features = self.backbone(x)
        features = features.flatten(1)

        return self.head(features)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public builder

def build_model(config : dict, in_channels : int, in_hw : tuple, num_classes : int) -> nn.Module :
    """
    Build the experiment model from a configuration.

    Parameters
    ----------
    config : dict
        The experiment configuration.
    in_channels : int
        Number of channels of the input images.
    in_hw : tuple
        Spatial size ``(height, width)`` of the input images.
    num_classes : int
        Number of output classes.

    Returns
    -------
    model : torch.nn.Module
        The assembled model.
    """

    return configurable_net(config, in_channels, in_hw, num_classes)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _build_backbone(config : dict, in_channels : int) -> nn.Module :
    """
    Build the (optional) convolutional backbone.

    When ``use_cnn_backbone`` is ``False`` an identity module is returned so the input flows straight to the head.

    Parameters
    ----------
    config : dict
        The experiment configuration.
    in_channels : int
        Number of channels of the input images.

    Returns
    -------
    backbone : torch.nn.Module
        The convolutional backbone (or an identity module).
    """

    if not config["use_cnn_backbone"] :
        return nn.Identity()

    layers          = []
    current_channels = in_channels

    # Each block : conv -> (batch-norm) -> activation -> (dropout) -> pooling.
    for layer_index in range(config["n_cnn_layer"]) :
        out_channels = config["cnn_layer_size"][layer_index]

        layers.append(
            nn.Conv2d(current_channels, out_channels, kernel_size = CONV_KERNEL_SIZE, padding = CONV_PADDING)
        )

        if config["batch_norm_cnn"] :
            layers.append(nn.BatchNorm2d(out_channels))

        layers.append(build_activation(config["activation_function"]))

        if config["dropout_2d_rate"] > 0.0 :
            layers.append(nn.Dropout2d(config["dropout_2d_rate"]))

        layers.append(nn.MaxPool2d(kernel_size = config["pool_layer_size"][layer_index]))

        current_channels = out_channels

    return nn.Sequential(*layers)

def _build_head(config : dict, flattened_size : int, num_classes : int) -> nn.Module :
    """
    Build the fully-connected classification head.

    Parameters
    ----------
    config : dict
        The experiment configuration.
    flattened_size : int
        Number of input features (the flattened backbone output).
    num_classes : int
        Number of output classes.

    Returns
    -------
    head : torch.nn.Module
        The fully-connected head ending in one logit per class.
    """

    layers       = []
    current_size = flattened_size

    # Each block : linear -> (batch-norm) -> activation -> (dropout).
    for layer_index in range(config["n_fc_layer"]) :
        out_size = config["fc_layer_size"][layer_index]

        layers.append(nn.Linear(current_size, out_size))

        if config["batch_norm_fc"] :
            layers.append(nn.BatchNorm1d(out_size))

        layers.append(build_activation(config["activation_function"]))

        if config["dropout_rate"] > 0.0 :
            layers.append(nn.Dropout(config["dropout_rate"]))

        current_size = out_size

    # Final projection to the class logits (no activation : raw scores).
    layers.append(nn.Linear(current_size, num_classes))

    return nn.Sequential(*layers)
