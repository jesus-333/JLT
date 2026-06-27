# File Writing

While writing the instructions to run the experiment, I realized it would be convenient to have a function for creating text files internally within this package.
The idea I had in mind is the following.

A generic function `write_file(text : str, extension : str = 'txt')` that creates a file with the given input text and the specified extension.
The possible extensions for now are only `txt` and `md`. If not specified, it defaults to `txt`.
If you think it appropriate, you can choose a different name if you feel it causes less confusion or is more fitting.

An internal function within the backends used by LLMs to write files.
E.g. I need to update a config file of an experiment for the autoresearch tool. So the LLM will need to be able to read and modify a file based on what it has been asked.

Once done, update any files in the wiki.
