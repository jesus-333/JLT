# Example `autoresearch` experiment — classic machine learning (scikit-learn)

A runnable, end-to-end example for the `jlt autoresearch run` command that uses **classic
machine-learning models from scikit-learn instead of neural networks**. It is the non-NN
counterpart of [`examples/autoresearch_nn/`](../autoresearch_nn) and trains on the **same
combined dataset** (FashionMNIST + KMNIST + EMNIST + CIFAR10), so the two examples differ only
in the kind of model and in how the configuration is organised.

This example has a **double purpose** :

1. show that `autoresearch` works just as well with non-neural-network code ;
2. exercise how `autoresearch` handles an experiment with **multiple configuration files**.

The metric `autoresearch` optimises is the **top-1 accuracy on the validation set** (maximise).

## Multiple config files

The experiment is deliberately split across several files in `combined/config/` :

```
combined/config/
    general.toml              # COMMON settings : seed, data subsample sizes,
                              #   shared preprocessing, and the `classifier` selector
    logistic_regression.toml  # all hyperparameters of LogisticRegression
    random_forest.toml        # all hyperparameters of RandomForestClassifier
    svm.toml                  # all hyperparameters of SVC
    knn.toml                  # all hyperparameters of KNeighborsClassifier
    decision_tree.toml        # all hyperparameters of DecisionTreeClassifier
    gradient_boosting.toml    # all hyperparameters of GradientBoostingClassifier
```

`general.toml` holds everything common to all classifiers (the seed being the obvious example)
plus a `classifier` key that selects **which** algorithm is trained this round. Each algorithm
then has its own file with all of its hyperparameters.

Every round `autoresearch` may edit **any** of these files (only the *values*, never the set of
keys — it enforces this). To improve the metric the optimiser can switch algorithm (change
`classifier` in `general.toml`), tune the active algorithm's own file, and/or tune the shared
preprocessing in `general.toml`. Only the selected algorithm's file plus `general.toml` affect a
given round, so the other files are simply left unchanged that round — which is exactly the
multi-config behaviour this example is meant to show.

## Layout

```
examples/autoresearch_sklearn/
    common/      shared code : data pipeline, classifier factory, train/evaluate pipeline
    combined/    the experiment (run.py + config/ + experiment_description.md)
    data/        torchvision downloads (created on first run, gitignored)
```

`run.py` adds `common/` to `sys.path` and calls the shared pipeline, keeping the registered
experiment folder limited to `run.py`, its `config/` folder and the description.

## Requirements

```bash
pip install -r examples/autoresearch_sklearn/requirements.txt
# CPU-only torch (used only to download/decode the datasets) :
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

Running a round also needs a configured, active LLM backend (see `jlt backend`) and a network
connection — `torchvision` downloads the datasets on first use (EMNIST and CIFAR10 are large).
Merely **registering** the experiment needs none of this : `run.py` is only parsed statically.

## Usage

```bash
# Register the experiment, maximising accuracy
jlt ar add --path_folder examples/autoresearch_sklearn/combined --metric_name accuracy --ascending

# Or read everything from the provided info file (run from this folder)
# jlt ar add --experiment_info_path experiment_info_file.toml

# Run one optimisation round (needs an active backend)
jlt ar run --experiment_name combined
```

Each `run` reads the logs, lets the LLM tweak the config files, trains the selected classifier,
records the accuracy and updates the logs. Repeat `jlt ar run ...` for further rounds. See the
[autoresearch summary](../../llm_wiki/summaries/autoresearch.md) and the
[run deep-dive](../../llm_wiki/detailed_descriptions/autoresearch_run.md) for what happens during
a round.

## The data

The four `torchvision` datasets are harmonised to grayscale 28×28 images, flattened to
784-dimensional feature vectors, and restricted to a fixed selection of 10 classes spanning all
four datasets (re-mapped to `0..9`). A small deterministic subsample is taken from each dataset
(sizes in `general.toml`) so a round stays fast. `num_classes` is derived from the data (10),
not configured.
