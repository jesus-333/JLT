Okay. Iniziamo a lavorare sulla backend per gestire gli llm.

Deve essere ovvimante un sottocomando di `jlt` che sia chiama con `jlt backend`

A livello di codice python ci deve essere la seguente struttura

```
src/
    jlt/
        cli.py                  ---> Top-level CLI entry point (the jlt command)
        tool_1/                 ---> Source code for tool 1
            cli.py              ---> CLI entry point for tool_1
            ...
        ...
        tool_n/                 ---> Source code for tool n
            cli.py              ---> CLI entry point for tool_n
            ...
        shared_knowledge/       ---> Source code shared by all tools
            backend/            ---> All the source code related to backend
                generic.py      ---> Generic abstract class for backend implementation. 
                backend_1.py    ---> Implementation of backend 1
                ...
                backend_n.py    ---> Implementation of backend n
                other_file...   ---> You could create other files if you think its necessary
```

Ho messo il codice della backend dentro `shared_knowledge` perchè molto probabilmente verrà riusato anche da altri tool in futuro.

`generic.py` deve essere una classe template astratta che permette di offrire un interfaccia unica al resto dei tool.
Deve esporre necessariamente questi metodi
- `update_config()` funzione per configurare la backend (chiamata anche dall `__init__()`). Deve ricevere in input un dizionario con tutte le configurazioni necessarie e salvarlo in qualche path dove il tool può andarlo a recuperare.
- `update_config_from_file()` funzione che riceve in inpput un path a un file contenente il dizionario, lo legge e poi usa `update_config` per aggiornare i config. Attualmente devono essere supportati `toml` and `json`. Puoi aggiungere altri formati se pensi sia utile
- `check_config()` funzione specifica per ogni backend che controlla che il dizionario di config vada bene. Chiamata da `update_config` prima di salvare i config.
- `__init__()` che ovviamente che riceve in input sempre il path al dizionario
- `modify_file(prompt : str, file to edit : str, other_files : str = None)` : modifica il file specificato in `file to edit ` seguendo il `prompt`. Quest'ultimo può essere sia le istruzioni direttamente o il path a un file di testo con le istruzioni. `other_file` per ora è un parametro in più. Non serve implementare nulla riguardo ad esso. Ma la mia idea è di averlo lì nel caso abbia qualche prompt del tipo "Ti ho passato tot file contenti delle istruzioni. Usale per modificare quest'altro file"
- `read_file(file_to_read : str, summarize : bool = False)` : Si limita a leggere un file di testo e tornarlo come stringa. Usata per esempio da `modify_file` nel caso il prompt sia passato come un path. Se `summarize` è settato su vero usa l'LLM per fare un riassunto di ciò che a letto. Non sono ancora sicuro in quali altri maniere possa utilizzarla in futuro ma preferisco averla qui.
- `read_files(list_of_files : list, summarize : bool = False)` : analogo di `read_file` ma per una lista di file. Tutti i file letti sono salvati su un unica stringa. Se `summarize` è settato su vero fa un riassunto di ogni file prima di salvarlo.

Ogni specifica backend dovrà essere figlia della classe `generic`

Attualmente voglio che siano implementate le seguenti backend :
- `ollama` (sia locale che cloud)
- `claude` (per tutti i modelli di anthropic)
- `chat_gpt` (per tutti i modelli di OpenAI)
- `github_copilot` (per interfacciarsi con github copilot)

Il comando da `cli` deve essere chiamato tramite `jlt backend`. Da qui ci devono essere ulteriori sottocomandi. Per oguno di essi ho specificato anche le flag.
- `config` : usato per configurare la backend
    - `--backend_name` : flag obbligatoria. Contiene il nome con cui viene salvata la backend.
    - `--path_file` : path ad un file config valido. Questa flag deve essere usata obbligatoriamente
- `list` : per mostrare tutte le backend configurate (può essere abbreviato con `ls`)
- `activate` : setta internamente al tool quale backend usare
    - `--backend_name` : flag obbligatoria. Specifica il nome della backend da usare. Se non è presente nell'elenco delle backend configurate da un errore.
- `remove` : rimuove la backend specificata (può essere abbreviato con `rm`)
    - `--backend_name` : flag obbligatoria. Specifica il nome della backend da rimuovere. Se non è presente nell'elenco delle backend configurate da un errore.

Nota che io posso avere più backend configurate per uno stesso provider. Ad esempio se ho due account di anthropic a pagamento io posso avere configurate 2 backend per claude (1 per account, con nomi diversi ovviamente)

Aggiorna anche `pyproject.toml` di conseguenza (nuove funzioni cli, pacchetti da installare etc). Aggiungi l'opzione di installare solo una specifica backend se l'utente vuole.
Ad esempio se sono interessato a usare `jlt` sono con claude dovrò poter fare `pip insall jlt[claude]`.

Se ci sono cose che non ti sono chiare prima di inizare a lavorare o hai bisogno di ulteriori istruzioni chiedi pure.
