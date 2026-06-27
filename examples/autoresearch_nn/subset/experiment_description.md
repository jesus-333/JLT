# Subset combined-dataset experiment (fast)

## Goal

A fast variant of the combined-dataset experiment, meant for quick `autoresearch` iteration.
Train an image classifier and **maximise the top-1 accuracy on the validation set**
(`--metric_name accuracy --ascending`).

## Data

- Same four `torchvision` datasets as the `full` experiment (FashionMNIST, KMNIST, EMNIST,
  CIFAR10), harmonised to **grayscale, 28×28, single channel**.
- Restricted to a **fixed selection of 10 classes spanning all four datasets** (so it stays a
  genuinely combined problem), re-mapped to `0..9`. The exact selection is documented in
  `run.py` (`SELECTED_GLOBAL_LABELS`).
- A small, **deterministic subsample** is taken from each dataset — at most 3000 train and 1000
  validation samples per dataset (see `SUBSET_TRAIN_PER_DATASET` / `SUBSET_VAL_PER_DATASET` in
  `run.py`). This keeps a round to roughly one to a few minutes.
- Training uses each dataset's official **train** split, validation the **test** split.
- Datasets are downloaded on first run into `../data/` (shared with the `full` experiment).
  Note: `torchvision` always downloads the **whole** dataset; the subsampling only reduces what
  is *trained on*, not what is downloaded.

## Model

Identical configurable network as the `full` experiment (optional CNN backbone + FC head). All
architecture comes from `config/config.toml`.

## What the optimiser may tune

The keys in `config/config.toml`. Only the **values** may change between rounds — the set of
keys is fixed. `num_classes` is derived from the data (10 here), not configured.

## Round budget

At most `num_epochs` epochs **or 10 minutes** of wall-clock time, whichever comes first. With
the subsample this normally finishes all epochs well before the cap.
