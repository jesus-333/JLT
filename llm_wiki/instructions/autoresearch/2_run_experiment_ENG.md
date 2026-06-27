# Autoresearch — Experiment Execution (`run` command)

Now let's work on the experiment execution part: the `run` command.

The command must have the following flag:
- `--experiment_name` : mandatory flag. Specifies the name of the experiment to run (already implemented).


# Steps (high-level overview)

Once launched, the command works as follows. From inside the experiment folder:

1) The `experiment_description` file is read to get a general idea of what the experiment does.
2) The contents of the `jlt_log_<experiment_name>` folder are inspected:
    - The file `round_i.md` is produced, where `i` is the current round number.
    - The `summary_log.md` file is always read to understand how far previous experiments have progressed.
    - (OPTIONAL) Individual round reports may be read if additional context is needed.
    - Based on this analysis, the hyperparameters in the `config` folder are modified.
3) The experiment is launched.
4) Once the experiment has finished:
    - The metric is saved in `txt`/`csv` files that track the metric value at each round.
    - The `summary_log.md` file is updated/overwritten based on the results.
5) All results are also copied to the tool's internal backup (see previous instruction sheets for details if needed).

This is the general workflow. Several details are covered more thoroughly below.

# `round_i.md` File Template

A template file for `round_i.md` can be found [here](./template_round_i.md).

This is a template for the log files produced each round.
This template must be saved somewhere internally within the tool and used every time a new log is produced.

# Keeping Track of the Round

To keep track of the round number, there must be a `round.txt` file inside the `jlt_log_<experiment_name>` folder. This file contains a single number representing how many rounds have been executed so far.
At the end of each round, this number must be incremented by 1.

This was not fully thought through previously and will therefore require modifications to the `jlt autoresearch add` command as well.
Specifically, the `add` command must also create this file when registering an experiment. When created, the file must contain only a `0`, since obviously `0` rounds have been executed at that point.

# Reading and Analysing Files During a Round

All of these operations, within the same round, must be performed within the same LLM conversation, so that information is kept in memory.
Changes to config files must be made based on what was read in the log files.
The post-experiment update must be based on the result and on the notes from previous logs.

## Reading `summary_log.md` and Previous `round_i.md` Files

The `experiment_description` and `summary_log.md` files are mandatory reads every time.

Once done, the LLM must decide whether to also read the `round_i.md` files from previous rounds.
This step is optional. The implementation idea is as follows:
- After the `summary_log` analysis is complete, a message is sent to the LLM asking whether it wants to read the log files. The answer must be simply yes or no.
- If yes, it is asked which files it wants to read (it may be passed the list of filenames). The answer must strictly be a list of the files to read.
- The files are all loaded together and passed to the LLM.

Once the analysis of previous rounds is complete, the LLM must update the `round_i.md` file for the current round:
- In the `Summary Previous Rounds` section, it must write a very brief summary of all previous experiments (with optional references to previous logs if details are needed).
- In the `Experiment Configuration Update` section, it must describe how it wants to update the experiment's config files for this round, and why.


# Updating the Experiment Config Files

Once the desired changes to the experiment config files have been decided, the files must be updated.
The `modify_file` function already implemented inside the backend should be sufficient for this task.

However, I want to add some small improvements to make the process more robust.

Config files are simply dictionaries. Before being modified, `autoresearch` must create a backup copy of the config files.

After the dictionaries are modified, all keys in the new versions must be compared against the keys in the backup versions.
If there are any discrepancies, the modification did not succeed and must be redone.

# Running the Experiment

This part is fairly straightforward and simply consists of calling the `run` function that starts the experiment.

# Final Analysis

Once the results are obtained, an analysis of this round must be performed.
The analysis and conclusions must be saved in the `Result and analysis` section of the current `round_i` file.

# Synchronisation with the Tool's Internal Backup

Once the current round is complete, all results must be copied to the backup folder inside the tool.
Note: this step must be the very last thing performed.

Create a dedicated `sync` function for this purpose.
Optionally, also add the CLI command `jlt autoresearch sync`, which takes the results from the current experiment folder and copies them to the tool's internal backup folder.
This command must have two flags:
- `--experiment_name` : name under which to save the experiment. If not specified, the name of the folder where the files are stored is used.
- `--reverse` : optional boolean flag. If passed, it reverses the synchronisation direction: the files inside the tool's backup folder are copied into the experiment folder instead.
