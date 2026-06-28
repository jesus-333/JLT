# Combined-dataset experiment — classic machine learning (scikit-learn)

## Goal

Train a **classic machine-learning classifier** (no neural network) on a single multi-class
problem built by **combining four `torchvision` datasets** — FashionMNIST, KMNIST, EMNIST
(`balanced` split) and CIFAR10 — and **maximise the top-1 accuracy on the validation set**.

This is the metric `autoresearch` optimises (`--metric_name accuracy --ascending`).

## Data

- All four datasets are harmonised to **grayscale, 28×28, single channel** and then **flattened
  into a 784-dimensional feature vector** per image (CIFAR10 is converted to grayscale and
  resized).
- The problem is restricted to a **fixed selection of 10 classes spanning all four datasets**
  (so it stays a genuinely combined problem), re-mapped to `0..9`. The exact selection is
  documented in `run.py` (`SELECTED_GLOBAL_LABELS`).
- A small, **deterministic subsample** is taken from each dataset (sizes set in `general.toml`),
  because some classic models (e.g. the SVM) scale badly with the number of samples.
- Training uses each dataset's official **train** split, validation the **test** split.
- Datasets are downloaded on first run into `../data/`. `torchvision` always downloads the
  **whole** dataset; the subsampling only reduces what is *trained on*, not what is downloaded.

## Models

Six scikit-learn classifiers are available. Exactly **one** is trained per round, chosen by the
`classifier` key in `general.toml` :

| `classifier` value     | Estimator                       |
| ---------------------- | ------------------------------- |
| `logistic_regression`  | `LogisticRegression`            |
| `random_forest`        | `RandomForestClassifier`        |
| `svm`                  | `SVC`                           |
| `knn`                  | `KNeighborsClassifier`          |
| `decision_tree`        | `DecisionTreeClassifier`        |
| `gradient_boosting`    | `GradientBoostingClassifier`    |

Before the classifier, a shared preprocessing pipeline is applied : an optional
`StandardScaler` (`standardize`) followed by an optional `PCA` (`pca_components`, `0` to
disable). Both live in `general.toml` because they apply to every classifier.

## Configuration — several files

This experiment is **deliberately split across multiple config files** in `config/` :

- **`general.toml`** — hyperparameters common to every classifier : the `seed`, the data
  subsample sizes (`train_samples_per_dataset`, `val_samples_per_dataset`), the shared
  preprocessing (`standardize`, `pca_components`) and the **`classifier` selector** naming
  which algorithm to train this round.
- **`<classifier>.toml`** (one per algorithm) — all the hyperparameters of that single
  algorithm.

## What the optimiser may tune

Every config file is editable each round, but only the **values** may change — the set of keys
in each file is fixed (autoresearch enforces this). Concretely, to improve the metric you may :

1. **switch algorithm** by changing `classifier` in `general.toml` to another value from the
   table above, and/or
2. **tune the active algorithm** by editing the values in its `<classifier>.toml`, and/or
3. **tune the shared preprocessing / data size** in `general.toml`.

Only the config file named by `classifier` (plus `general.toml`) affects a given round; the
other algorithms' files are simply unused that round, so it is fine to leave them unchanged.

### Value conventions (TOML has no `null`)

- `max_depth = 0` means **no depth limit** (scikit-learn `None`).
- `max_features = "all"` (tree-based estimators) means **use every feature** (scikit-learn
  `None`); the other accepted values are `"sqrt"` and `"log2"`.

Keep value combinations valid for the chosen estimator (e.g. `degree` only matters for the SVM
`poly` kernel; `subsample < 1.0` turns gradient boosting stochastic).

## `num_classes`

`num_classes` is derived from the data (10 here), not configured.
