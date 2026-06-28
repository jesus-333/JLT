# Full combined-dataset experiment

## Goal

Train an image classifier on a single, large multi-class problem built by **combining four
`torchvision` datasets** — FashionMNIST, KMNIST, EMNIST (`balanced` split) and CIFAR10 — and
**maximise the top-1 accuracy on the validation set**.

This is the metric `autoresearch` optimises (`--metric_name accuracy --ascending`).

## Data

- All four datasets are harmonised to **grayscale, 28×28, single channel** (CIFAR10 is
  converted to grayscale and resized).
- Every class of every dataset is kept and offset into one global label space :
  `10 (FashionMNIST) + 10 (KMNIST) + 47 (EMNIST balanced) + 10 (CIFAR10) = 77 classes`.
- Training uses each dataset's official **train** split ; validation uses each dataset's
  official **test** split.
- The datasets are downloaded on first run into `../data/` (shared with the `subset`
  experiment). The EMNIST and CIFAR10 downloads are large.

## Model

A configurable network : an optional convolutional backbone (conv → optional batch-norm →
activation → optional 2D dropout → max-pool) followed by a fully-connected head ending in one
logit per class. Every architectural choice comes from `config/config.toml`.

## What the optimiser may tune

The keys in `config/config.toml` (architecture, optimiser, learning rate, batch size, epochs,
loss, scheduler, seed). Only the **values** may change between rounds — the set of keys is
fixed. `num_classes` is derived from the data, not configured.

## Round budget

Each round trains for at most `num_epochs` epochs **or 10 minutes of wall-clock time**,
whichever comes first (the time budget is checked every batch). On CPU the full dataset is
large, so a round will typically hit the time cap before finishing all epochs — that is
expected. For a faster turnaround use the sibling `subset` experiment.
