Okay, inizialmente volevo

Come suggerisce il nome questo deve una version cli dell'idea che karpathy ha avuto con l'[autoresearch](https://github.com/karpathy/autoresearch/tree/master).

Per ora il tool autoresearch deve avere 2 sottocomandi :
- `config_experiment`
- `run_experiment`


Il tool deve funzionare a grandi linee in questo modo 
0) L'utente configura la backend che vuole usare per LLM (ollama, claude, chatGPT etc)
1) L'utente crea i file per far runnare l'esperimento e li salva in una cartella.
2) autoresearch controlla i file, eventuali istruzioni extra date dall'utente e si crea un riassunto di quello che deve fare (`config_backend`). Questo passo è opzionale se l'utente si crea già un suo file di istruzioni da seguire.
3) La parte di running dell'esperimento (`run_experiment`)
    1. Un'istanza dell'LLM è creata e modica i setup dell'esperimento. Nota bene che il codice dell'esperimento non deve mai essere modificato. 
    2. autoresearch (programmaticamente e NON TRAMITE LLM) lancia l'esperimento
    3. Quando l'esperimento l'LLM analizza i risultati dell'esperimento e fa delle considerazioni per la prossima iterazione
    4. Questi step vengono ripetuti finchè un certo criterio di convergenza non è soddisfatto.
5) Un report finale viene prodotto

Ovviamente ci sono dettagli più complessi riguardo la parte `run_experiment` e `config_experiment` che ho ommesso qui (e.g. criterio di convergenza, struttura permessa degli esperimenti) ma che al momento non sono importanti.
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
