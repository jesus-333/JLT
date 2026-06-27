# Example `autoresearch` experiment — neural-network training

A runnable, end-to-end example for the `jlt autoresearch run` command. It trains a configurable
PyTorch image classifier on a dataset built by **combining four `torchvision` datasets**
(FashionMNIST, KMNIST, EMNIST, CIFAR10) and the metric `autoresearch` optimises is the
**top-1 accuracy on the validation set** (maximise).

There are **two experiments** sharing one code base :

| Experiment | Data | Classes | Speed |
| --- | --- | --- | --- |
| [`full/`](full) | full combined datasets, all classes | 77 (EMNIST `balanced`) | slow on CPU — usually hits the 10-min cap |
| [`subset/`](subset) | small subsample, 10 selected classes spanning all 4 datasets | 10 | fast — ~1–3 min/round |

Each round runs for at most `num_epochs` epochs **or 10 minutes** of wall-clock time, whichever
comes first.

## Layout

```
examples/autoresearch_nn/
    common/      shared code : factories, model, data pipeline, training loop
    full/        the full experiment (run.py + config/ + experiment_description.md)
    subset/      the fast subsampled experiment
    data/        torchvision downloads (created on first run, gitignored)
```

Each experiment's `run.py` adds `common/` to `sys.path` and calls the shared pipeline, so the
two differ only in how they wire it (which classes / how many samples).

## Requirements

```bash
pip install -r examples/autoresearch_nn/requirements.txt
# CPU-only torch:
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

Running a round also needs a configured, active LLM backend (see `jlt backend`) and a network
connection — `torchvision` downloads the datasets on first use (EMNIST and CIFAR10 are large).
`torchvision` always downloads the *whole* dataset; the `subset` experiment only subsamples what
is *trained on*, not what is downloaded.

## Usage

Register an experiment, then run one optimisation round :

```bash
# Fast variant (recommended to try first)
jlt ar add --path_folder examples/autoresearch_nn/subset --metric_name accuracy --ascending
jlt ar run --experiment_name subset

# Full variant
jlt ar add --path_folder examples/autoresearch_nn/full --metric_name accuracy --ascending
jlt ar run --experiment_name full
```

Each `run` reads the logs, lets the LLM tweak `config/config.toml`, trains the model, records the
accuracy and updates the logs. Repeat `jlt ar run ...` to perform further rounds. See the
[autoresearch summary](../../llm_wiki/summaries/autoresearch.md) and the
[run deep-dive](../../llm_wiki/detailed_descriptions/autoresearch_run.md) for what happens during
a round.

## The configuration

`config/config.toml` holds the hyperparameters the optimiser may tune (architecture, optimiser,
learning rate, batch size, epochs, loss, scheduler, seed). Only the **values** change between
rounds — the set of keys is fixed (autoresearch enforces this). `num_classes` is derived from the
data, not configured.
