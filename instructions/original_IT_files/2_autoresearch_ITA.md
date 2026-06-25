Okay, inizialmente volevo

Come suggerisce il nome questo deve una version cli dell'idea che karpathy ha avuto con l'[autoresearch](https://github.com/karpathy/autoresearch/tree/master).

Il tool deve funzionare a grandi linee in questo modo 
0) L'utente configura la backend che vuole usare per LLM (ollama, claude, chatGPT etc)
1) L'utente crea i file per far runnare l'esperimento e li salva in una cartella.
2) autoresearch controlla i file, eventuali istruzioni extra date dall'utente.
3) La parte di running dell'esperimento.
    1. Un'istanza dell'LLM è creata e modica i setup dell'esperimento. Nota bene che il codice dell'esperimento non deve mai essere modificato. 
    2. autoresearch (programmaticamente e NON TRAMITE LLM) lancia l'esperimento
    3. Quando l'esperimento l'LLM analizza i risultati dell'esperimento e fa delle considerazioni per la prossima iterazione
    4. Questi step vengono ripetuti finchè un certo criterio di convergenza non è soddisfatto.
5) Un report finale viene prodotto

Ovviamente ci sono dettagli molto più complessi che ho ommesso qui (e.g. criterio di convergenza, struttura permessa degli esperimenti). 
Li discuteremo quando andremo a implementare quelle specifiche componenti (o sottocomponenti).

A livello di codice python ci deve essere la seguente struttura

```
src/
    jlt/
        cli.py                  ---> Top-level CLI entry point (the jlt command)
        autoresearch/           ---> Source code for tool 1
            cli.py              ---> CLI entry point for autoresearch
            config_experiment/  ---> Code related to experiment configuraion. To be implemented in future.
            run_experiment/     ---> Code related to running experiment. To be implemented in future.
        shared_knowledge/       ---> Source code shared by all tools
            ...
```

Il comando da `cli` deve essere chiamato tramite `jlt backend`. Da qui ci devono essere ulteriori sottocomandi. Per oguno di essi ho specificato anche le flag.
- `add` : usato per configurare la l'esperimento. Da notare che questo comando non crea una copia dei file dell'esperimento ma semplicemente ne salva il path internamente al tool.
    - `--path_folder` : path ad un file config valido. Questa flag deve essere usata obbligatoriamente. 
    - `--experiment_name`: nome con cui salvare l'esperimento. Se non specificato viene usato quella della cartella dove sono salvati i file.
- `list` : per mostrare tutti gli esperimenti nel registro (può essere abbreviato con `ls`)
- `remove` : rimuove dal registro l'esperimento specificaot (può essere abbreviato con `rm`)
    - `--experiment_name` : flag obbligatoria. Specifica il nome dell'esperimento da rimuovere
