"""
Combined dataset builder for the sklearn ``autoresearch`` example.

The "dataset" of this example is exactly the same combined dataset used by the neural-network example (see ``examples/autoresearch_nn``) : the concatenation of four ``torchvision`` datasets (FashionMNIST, KMNIST, EMNIST and CIFAR10).
The difference is the output format : classic scikit-learn estimators want plain feature matrices, so every image is harmonized to a grayscale 28x28 picture and then **flattened into a 784-dimensional feature vector**, and the whole split is returned as a single ``numpy`` array ``(n_samples, 784)`` together with its integer labels.

The labels of the four datasets are offset into one global label space so the classifier sees a single multi-class problem.
To keep a round fast (some sklearn models, e.g. the SVM, scale badly with the number of samples) the builder restricts the problem to a fixed selection of global labels (re-mapped to ``0..k-1``) and takes a small, deterministic subsample of each dataset.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Specific imports
import numpy as np
from torchvision import datasets, transforms

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Common input geometry every image is resized / converted to before flattening.
IMAGE_SIZE  = (28, 28)
IN_CHANNELS = 1

# Number of features of a flattened image (1 channel x 28 x 28).
NUM_FEATURES = IN_CHANNELS * IMAGE_SIZE[0] * IMAGE_SIZE[1]

# Number of classes contributed by each EMNIST split (used to compute label offsets).
EMNIST_NUM_CLASSES = {
    "byclass" : 62, "bymerge" : 47, "balanced" : 47, "letters" : 26, "digits" : 10, "mnist" : 10,
}

# The shared preprocessing : everything ends up as a normalized 1x28x28 tensor in
# ``[0, 1]``. ``Grayscale`` turns CIFAR10 (RGB) into a single channel and leaves the
# already grayscale MNIST-family images untouched.
TRANSFORM = transforms.Compose([
    transforms.Grayscale(num_output_channels = IN_CHANNELS),
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public builder

def build_combined_dataset(
        *,
        seed                       : int,
        data_root                  : str,
        emnist_split               : str = "balanced",
        train_samples_per_dataset  : int | None = None,
        val_samples_per_dataset    : int | None = None,
        selected_global_labels     : list | None = None,
    ) -> tuple :
    """
    Build the combined train / validation feature matrices and report the number of classes.

    Parameters
    ----------
    seed : int
        Seed driving the deterministic subsampling.
    data_root : str
        Directory where the ``torchvision`` datasets are downloaded / cached.
    emnist_split : str, default ``"balanced"``
        Which EMNIST split to use (one of the keys of :data:`EMNIST_NUM_CLASSES`).
    train_samples_per_dataset : int or None, default ``None``
        Maximum number of samples to keep from each dataset's train split. ``None`` keeps all of them.
    val_samples_per_dataset : int or None, default ``None``
        Maximum number of samples to keep from each dataset's test split. ``None`` keeps all of them.
    selected_global_labels : list or None, default ``None``
        If given, only samples whose global label is in this list are kept, and the labels are re-mapped to ``0..k-1``. If ``None`` every class is kept.

    Returns
    -------
    x_train : numpy.ndarray
        Training features of shape ``(n_train, 784)`` in ``[0, 1]``.
    y_train : numpy.ndarray
        Training integer labels of shape ``(n_train,)``.
    x_val : numpy.ndarray
        Validation features of shape ``(n_val, 784)`` in ``[0, 1]``.
    y_val : numpy.ndarray
        Validation integer labels of shape ``(n_val,)``.
    num_classes : int
        Number of output classes (the global label space size, or the selection size in subset mode).

    Raises
    ------
    ValueError
        If ``emnist_split`` is not one of the known splits.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Resolve the label space

    if emnist_split not in EMNIST_NUM_CLASSES :
        raise ValueError(
            f"Unknown EMNIST split '{emnist_split}'. Expected one of {sorted(EMNIST_NUM_CLASSES)}."
        )

    # Per-dataset specification : (name, class, extra kwargs, number of classes).
    specs = [
        ("fashion", datasets.FashionMNIST, {},                       10),
        ("kmnist",  datasets.KMNIST,       {},                       10),
        ("emnist",  datasets.EMNIST,       {"split" : emnist_split}, EMNIST_NUM_CLASSES[emnist_split]),
        ("cifar10", datasets.CIFAR10,      {},                       10),
    ]

    total_classes = sum(spec[3] for spec in specs)

    # In subset mode the kept labels are compacted to ``0..k-1``.
    if selected_global_labels is not None :
        label_map   = {global_label : new_label for new_label, global_label in enumerate(sorted(selected_global_labels))}
        num_classes = len(label_map)
    else :
        label_map   = None
        num_classes = total_classes

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Build both splits

    x_train, y_train = _build_split(specs, emnist_split, data_root, True,  train_samples_per_dataset, selected_global_labels, label_map, seed)
    x_val,   y_val   = _build_split(specs, emnist_split, data_root, False, val_samples_per_dataset,   selected_global_labels, label_map, seed + 1)

    return x_train, y_train, x_val, y_val, num_classes

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _build_split(
        specs, emnist_split : str, data_root : str, train : bool,
        max_per_dataset : int | None, selected_global_labels : list | None,
        label_map : dict | None, seed : int,
    ) -> tuple :
    """
    Build one concatenated split (train or validation) from every dataset.

    Parameters
    ----------
    specs : list
        The per-dataset specifications (name, class, extra kwargs, class count).
    emnist_split : str
        The EMNIST split being used (needed for the 1-indexed ``letters`` fix).
    data_root : str
        Download / cache directory.
    train : bool
        Whether to load the training split (``True``) or the test split (``False``).
    max_per_dataset : int or None
        Maximum number of samples to keep from each dataset (``None`` for all).
    selected_global_labels : list or None
        Global labels to keep (``None`` for all).
    label_map : dict or None
        Mapping to compact labels (``None`` when every class is kept).
    seed : int
        Seed for the deterministic subsampling.

    Returns
    -------
    features : numpy.ndarray
        The concatenated, flattened features of shape ``(n_samples, 784)``.
    labels : numpy.ndarray
        The corresponding integer labels of shape ``(n_samples,)``.
    """

    selected_set = set(selected_global_labels) if selected_global_labels is not None else None

    feature_blocks = []
    label_blocks   = []
    offset         = 0

    for name, dataset_class, extra_kwargs, class_count in specs :

        # Build the base dataset (downloading on first use).
        base = dataset_class(root = data_root, train = train, download = True, transform = TRANSFORM, **extra_kwargs)

        letters_fix = (name == "emnist" and emnist_split == "letters")

        # Decide which base indices to keep : optional label filter then optional subsample.
        indices = _select_indices(base, offset, letters_fix, selected_set, max_per_dataset, seed)

        # Materialize the selected samples as flattened feature vectors. Only the
        # selected indices are transformed, so the heavy resize / grayscale work is
        # paid only for the (small) subsample that is actually trained on.
        for index in indices :
            image, raw_label = base[index]
            global_label     = _to_global_label(int(raw_label), offset, letters_fix)

            if label_map is not None :
                global_label = label_map[global_label]

            feature_blocks.append(image.numpy().reshape(-1))
            label_blocks.append(global_label)

        offset += class_count

    features = np.asarray(feature_blocks, dtype = np.float32)
    labels   = np.asarray(label_blocks,   dtype = np.int64)

    return features, labels

def _select_indices(
        base, offset : int, letters_fix : bool, selected_set : set | None,
        max_per_dataset : int | None, seed : int,
    ) -> list :
    """
    Return the base indices to keep for one dataset (after filtering and subsampling).

    Parameters
    ----------
    base : torch.utils.data.Dataset
        The underlying dataset.
    offset : int
        Label offset of this dataset in the global label space.
    letters_fix : bool
        Whether the raw labels are 1-indexed (EMNIST ``letters``).
    selected_set : set or None
        Global labels to keep (``None`` keeps all).
    max_per_dataset : int or None
        Maximum number of samples to keep (``None`` keeps all).
    seed : int
        Seed for the deterministic subsample.

    Returns
    -------
    indices : list
        The selected base indices.
    """

    raw_labels = _raw_targets(base)

    # Filter by global label if a selection was requested.
    if selected_set is None :
        indices = list(range(len(raw_labels)))
    else :
        indices = [
            index
            for index, raw_label in enumerate(raw_labels)
            if _to_global_label(int(raw_label), offset, letters_fix) in selected_set
        ]

    # Deterministically subsample if a cap was requested.
    if max_per_dataset is not None and len(indices) > max_per_dataset :
        rng     = np.random.RandomState(seed)
        indices = rng.permutation(indices)[:max_per_dataset].tolist()

    return indices

def _raw_targets(base) -> list :
    """
    Return the raw integer labels of a dataset as a plain list.

    ``torchvision`` exposes targets either as a tensor (MNIST-family) or as a python list (CIFAR10) ; this normalizes both to a list of ints.

    Parameters
    ----------
    base : torch.utils.data.Dataset
        The dataset whose targets are requested.

    Returns
    -------
    targets : list
        The raw integer labels.
    """

    targets = base.targets

    if isinstance(targets, list) :
        return targets

    # Tensor (MNIST-family) : convert once to a python list.
    return targets.tolist()

def _to_global_label(raw_label : int, offset : int, letters_fix : bool) -> int :
    """
    Map a raw dataset label to the global label space.

    Parameters
    ----------
    raw_label : int
        The label as returned by the dataset.
    offset : int
        The dataset's offset in the global label space.
    letters_fix : bool
        Whether to subtract 1 first (EMNIST ``letters`` is 1-indexed).

    Returns
    -------
    global_label : int
        The label in the global label space.
    """

    if letters_fix :
        raw_label -= 1

    return raw_label + offset
