Ora dobbiamo occuparsi della parte di configurazione degli esperimenti quindi dell'implementazione effettiva di questi 3 comandi
- `add` : usato per configurare la l'esperimento. Da notare che questo comando non crea una copia dei file dell'esperimento ma semplicemente ne salva il path internamente al tool.
- `list` : per mostrare tutti gli esperimenti nel registro (può essere abbreviato con `ls`)
- `remove` : rimuove dal registro l'esperimento specificaot (può essere abbreviato con `rm`)

# Note generali

Per esperimento si intende un processo di ottimizzazione iterativo di iperparametri. 
Ovviamente dato che è un processo iterativo, per uno stesso esperimento questa processo può essere ripetuto più e più volte (`round`).

Innazitutto `autoresearch` dovrà avere un qualcosa per tenere traccia di tutti gli esperimenti salvati.
Puoi usare lo stesso metodo che hai usato per tenere traccia delle backend. Una sorta di registro interno al tool.
Più info sul registro in fondo al file.

Per esperimento si intende una cartella con dentro degli script. 
Questi script possono fare qualsiasi cosa, e.g. simulazione numerica, training di una rete neurale, etc etc).

Questa cartella al suo interno dovrà avere tassativamente due cose
- Una sottocartella chiamata `config`. Qui saranno salvati tutti i file di configurazione necessari agli esperimenti. Per ora solo `toml` e `json` sono ammessi.
- Uno script chiamato `run.py` che fa partire l'esperiment. Per ora può essere solo on un file `python`
    - Questo file python deve avere un main all'interno che ritorna un valore numerico (la metrica che `autoresearch` deve migliorare)
    - `autoresearch`, quando il comando run sarà implementato dovrà eseguire proprio questo file qui di `run`

# Comando `add`

Il comando `add` avrà i seguenti flag
- `--path_folder` : path ad un file config valido. Questa flag deve essere usata obbligatoriamente (già implementato)
- `--experiment_name`: nome con cui salvare l'esperimento. Se non specificato viene usato quella della cartella dove sono salvati i file (già implementato)
- `--metric_name` : nome della metrica che dovrà ottimizzare (nuova flag) (obbligatoria)
- `--ascending` : specifica che la metrica dovrà essere incrmentata. Non può essere passato assieme a `--descending` (nuova flag) (obbligatoria)
- `--descending` : specifica che la metrica dovrà essere incrmentata. Non può essere passato assieme a `--ascending` (nuova flag) (obbligatoria)

Alternativamente, può passare un'unica flag chiamata `--experiment_info_path` che conterrà il path a un file `json` o `toml` al cui interno ci dovranno essere tutti i campi sopracitati.
Va da se che se `--experiment_info_path` nessuna altra flag può essere passata.

Una volta ricevuto il path dove sono salvati i file dell'esperimento
- Che il path sia valido e che la cartella esista
- Che ci sia la sottocartella `config`
- che ci sia lo script `run.py`
    - Che al suo interno ci sia una funzione `run`
    - Controllare che la funzione `run` ritorni un valore.
        - Per farlo usa AST (Abstract Syntax Tree), ti ho messo un esempio qua sotto
            - Se non c'è un return raise an error.
        - Se ha un return value controlla tramite annotazione che sia un valore numerico (ti ho incollato un altro esempio sotto)
            - Se l'operazione riesce è il tipo ritornato è un valore numerico ok
            - Se non è un valore numerico raise an error
            - Se non ci sono annotazioni fai passare la cosa ma genera un warning che dica che non è stato possibile verificare il tipo di ritorno della funzione e che l'utente deve essere sicuro che sia un valore numeric.

Una volta finiti i controlli dovrà creare una cartella chiamata `jlt_log_<experiment_name>` dove saranno salvati in futuro tutti i log creati automaticamente da `autoresearch`.
Per `<experiment_name>` si intende il nome dell'esperimento specificato dalla flag `--experiment_name`
Aggiungi anche un file chiamato `summary_log.md` che servirà in futuro a contenere il riassunto di tutti gli esperimenti fatti. 
Dato che al momento della sua creazione nessun esperimento è stato effettuato limitati a scriverci dentro "Nessun esperimento eseguito attualmente".
Aggiungi un semplice readme in txt o markdown all'interno della cartella che ne spieghi lo scopo.

## Check return value AST

Questo è solo un esempio. Se hai una soluzione più elegante implementala pure.

```python
import ast
import inspect
import textwrap

def has_return_value(func):
    source = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and node.value is not None:
            return True
    return False
```

## Check return value through annotation

Questo è solo un esempio. Se hai una soluzione più elegante implementala pure.

```python
import inspect

def get_return_annotation(func):
    sig = inspect.signature(func)
    return sig.return_annotation is not inspect.Parameter.empty
```

# Comandi `list` and `remove`

Questi comandi sono abbastanza esplicativi. 

`list` mostra tutti gli esperimenti salvati nel registo 

`remove` rimuove un esperimento dal registro. N.b. rimuove soltanto l'esperimento dal registro, non cancella fisicamente la cartella.

# Funzionamento del registro

(Questo è ancora temporaneo e può essere cambiato in corso d'opera)

Il registro deve tenere traccia di dove sono gli esperimenti e dei risultati ottenuti.

Per ogni esperimento dovrà salvare in un file `csv` e in un file `txt` il valore numerico della metrica dopo ogni `round` 
E.g. con il file `txt`
```txt
1, 0.4532
2, 0.4766
3, 0.5811
4, 0.6101
```

Per ogni round inoltre sarà prodotto un file di `log` con considerazioni riguardo all'esperimento e al processo di ottimizzazione.
I file avranno nome `round_i.md` dove `i` sarà sostituito dal numero del round. 
Ovviamente adesso non devi implementare la creazione di questi file (sarà fatto più avanti quando lavoreremo sull'implementazione di `run`) ma volevo che tu sapessi che esistevano.
Oltre ai file di `log` per ogni giorno ci sarà anche un file di log riassuntivo (`summary_log.md`) che sarà aggiornato alla fine di ogni esperimento.

Tutte queste informazioni dovranno essere salvata nella cartella `jlt_log_<experiment_name>` e in una cartella interna al tool con nome `<experiment_name>`.

La logica di questo sdoppiamento dell'informazione è avere un backup interno al tool nel caso la cartella con gli esperimenti vada persa, debba essere cancellata etc.
O anche il contrario... se per qualche motivo succede qualcosa alle cartelle del tool ci sarà una copia salvata dentro la cartella dell'esperimento



