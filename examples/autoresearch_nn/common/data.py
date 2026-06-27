"""
Combined dataset builder for the example experiment.

The "dataset" of this example is the concatenation of four ``torchvision`` datasets : FashionMNIST, KMNIST, EMNIST and CIFAR10.
They are harmonised to a single tensor shape (grayscale, 28x28, one channel) and their labels are offset into one global label space so the model sees a single multi-class classification problem.

Two modes are supported through the function arguments :

- **full** : keep every class of every dataset (the global label space) and every sample ;
- **subset** : keep only a fixed selection of global labels (re-mapped to ``0..k-1``) and a small, deterministic subsample of each dataset, so a round trains quickly.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Specific imports
import numpy as np
from torch.utils.data import ConcatDataset, DataLoader, Dataset
from torchvision import datasets, transforms

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Common input geometry every image is resized / converted to.
IMAGE_SIZE   = (28, 28)
IN_CHANNELS  = 1

# Number of classes contributed by each EMNIST split (used to compute label offsets).
EMNIST_NUM_CLASSES = {
    "byclass" : 62, "bymerge" : 47, "balanced" : 47, "letters" : 26, "digits" : 10, "mnist" : 10,
}

# The shared preprocessing : everything ends up as a normalised 1x28x28 tensor.
# ``Grayscale`` turns CIFAR10 (RGB) into a single channel and leaves the already
# grayscale MNIST-family images untouched.
TRANSFORM = transforms.Compose([
    transforms.Grayscale(num_output_channels = IN_CHANNELS),
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,)),
])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Dataset wrapper

class _label_mapped_dataset(Dataset) :
    """
    Wrap a base dataset, exposing only selected indices and re-labelled targets.

    Parameters
    ----------
    base : torch.utils.data.Dataset
        The underlying ``torchvision`` dataset.
    indices : list
        The base indices this wrapper exposes (used for filtering / subsampling).
    offset : int
        Value added to each raw label to move it into the global label space.
    letters_fix : bool
        If ``True`` subtract ``1`` from each raw label (EMNIST ``letters`` is 1-indexed).
    label_map : dict or None
        Optional mapping from global label to a compact ``0..k-1`` label (used in subset mode).
    """

    def __init__(self, base, indices : list, offset : int, letters_fix : bool, label_map : dict | None) -> None :
        """
        Store the base dataset and the re-labelling parameters.
        """

        self.base        = base
        self.indices     = indices
        self.offset      = offset
        self.letters_fix = letters_fix
        self.label_map   = label_map

    def __len__(self) -> int :
        """
        Return the number of exposed samples.
        """

        return len(self.indices)

    def __getitem__(self, index : int) :
        """
        Return the image and its (global, possibly re-mapped) label.
        """

        image, raw_label = self.base[self.indices[index]]
        global_label     = _to_global_label(int(raw_label), self.offset, self.letters_fix)

        if self.label_map is not None :
            global_label = self.label_map[global_label]

        return image, global_label

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public builder

def build_combined_loaders(
        *,
        batch_size              : int,
        seed                    : int,
        data_root               : str,
        emnist_split            : str = "balanced",
        subset_per_dataset      : tuple | None = None,
        selected_global_labels  : list | None = None,
        num_workers             : int = 0,
    ) -> tuple :
    """
    Build the combined train / validation loaders and report the number of classes.

    Parameters
    ----------
    batch_size : int
        Mini-batch size for both loaders.
    seed : int
        Seed driving the deterministic subsampling.
    data_root : str
        Directory where the ``torchvision`` datasets are downloaded / cached.
    emnist_split : str, default ``"balanced"``
        Which EMNIST split to use (one of the keys of :data:`EMNIST_NUM_CLASSES`).
    subset_per_dataset : tuple or None, default None
        If given, a ``(train_n, val_n)`` pair : the maximum number of samples to keep from each dataset's train / test split. If ``None`` the whole datasets are used.
    selected_global_labels : list or None, default None
        If given, only samples whose global label is in this list are kept, and the labels are re-mapped to ``0..k-1``. If ``None`` every class is kept.
    num_workers : int, default 0
        Number of worker processes for the data loaders.

    Returns
    -------
    train_loader : torch.utils.data.DataLoader
        Loader over the (shuffled) combined training set.
    val_loader : torch.utils.data.DataLoader
        Loader over the combined validation (test) set.
    num_classes : int
        Number of output classes (the global label space size, or the selection size in subset mode).
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

    train_n = subset_per_dataset[0] if subset_per_dataset is not None else None
    val_n   = subset_per_dataset[1] if subset_per_dataset is not None else None

    train_dataset = _build_split(specs, emnist_split, data_root, True,  train_n, selected_global_labels, label_map, seed)
    val_dataset   = _build_split(specs, emnist_split, data_root, False, val_n,   selected_global_labels, label_map, seed + 1)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Wrap in data loaders

    train_loader = DataLoader(train_dataset, batch_size = batch_size, shuffle = True,  num_workers = num_workers)
    val_loader   = DataLoader(val_dataset,   batch_size = batch_size, shuffle = False, num_workers = num_workers)

    return train_loader, val_loader, num_classes

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _build_split(
        specs, emnist_split : str, data_root : str, train : bool,
        max_per_dataset : int | None, selected_global_labels : list | None,
        label_map : dict | None, seed : int,
    ) -> ConcatDataset :
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
    dataset : torch.utils.data.ConcatDataset
        The concatenation of every dataset's selected, re-labelled samples.
    """

    selected_set = set(selected_global_labels) if selected_global_labels is not None else None

    wrapped_datasets = []
    offset           = 0

    for name, dataset_class, extra_kwargs, class_count in specs :

        # Build the base dataset (downloading on first use).
        base = dataset_class(root = data_root, train = train, download = True, transform = TRANSFORM, **extra_kwargs)

        letters_fix = (name == "emnist" and emnist_split == "letters")

        # Decide which base indices to keep : optional label filter then optional subsample.
        indices = _select_indices(base, offset, letters_fix, selected_set, max_per_dataset, seed)
        wrapped_datasets.append(_label_mapped_dataset(base, indices, offset, letters_fix, label_map))

        offset += class_count

    return ConcatDataset(wrapped_datasets)

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
        rng = np.random.RandomState(seed)
        indices = rng.permutation(indices)[:max_per_dataset].tolist()

    return indices

def _raw_targets(base) -> list :
    """
    Return the raw integer labels of a dataset as a plain list.

    ``torchvision`` exposes targets either as a tensor (MNIST-family) or as a python list (CIFAR10) ; this normalises both to a list of ints.

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
