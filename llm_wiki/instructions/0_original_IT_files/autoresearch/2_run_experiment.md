Ora lavoriamo sulla parte di esecuzione degli esperimenti, il comando `run`

Il comando deve avere le seguenti flag
    - `--experiment_name` : flag obbligatoria. Specifica il nome dell'esperimento da eseguire (già implementata)


# Step (a grandi linee)

Una volta lanciato il comando funziona in questo modo. Dall'interno della cartella dell'esperimento :
1) Viene letto il file `experiment_description` per avere un'idea generica di cosa fa l'esperimento
2) Controlla il contenuto della cartella `jlt_log_<experiment_name>`
    - Viene prodotto il file `round_i.md` dove `i` è il numero attuale del round.
    - Legge sempre il file `summary_log.md` per capire dove sono arrivati i precedenti esperimenti.
    - (OPZIONALE) Legge i report di singoli giorni nel caso gli serva altro contesto.
    - In base a queste analisi vengono modificati gli iperparametri dei config dentro la cartella `config`
3) Viene lanciato l'esperimento
4) Una volta finito l'esperimento 
    - La metrica viene salvata nei file `txt`/`csv` che tengono traccia della metrica ad ogni `round`
    - Il file `summary_log.md` viene aggiornato/sovrascritto in base ai risultati.
5) Tutti i risultati sono copiati anche nel backup interno del tool (vedi precedenti fogli di istruzioni nel caso ti servano più dettagli)

Ora questo è il funzionamento generale. Ci sono vari dettagli che ora andrò a coprire meglio.

# Template file `round_i.md`

Puoi trovare un file template dei file `round_i.md` a [qui](./template_round_i.md).

Questo è un template dei file di log che vengono prodotti ogni round. 
Questo template dovrà essere salvato da qualche parte internamente al tool e usato ogni volta per produrre i nuovi log.

# Tenere traccia del round

Per tenere traccia del ruond ci deve essere un file `round.txt` internamente alla cartella `jlt_log_<experiment_name>` al cui interno è scritto un solo numero che rappresenta il numero di round eseguiti.
Alla fine di ogni round questo numero deve essere aumentato di 1.

Questa cosa non l'avevo pensata del tutto prima quindi richiederà anche delle modifiche al comando `jlt autoresearch add`.
Per la precisione il comando `add` dovrà creare anche questo file quando aggiunge un esperimento al registro. Quando creato il file deve avere dentro solo uno `0` perchè ovviamente sono stati eseguiti `0` round.

# Lettura analisi dei file durante un round
Tutte queste operazioni, all'interno dello stesso round, devono essere fatte all'interno della stessa discussione dell'LLM, in maniera che si mantengano in memoria.
Le modifiche ai file di config devono essere fatte in base a cosa è stato letto nei file di log.
L'update dopo l'esperimento deve essere fatto in base al risultato e alle note dei log precedenti.

## Lettura `summary_log.md` e precedenti `round_i.md`
I file `experiment_description` e `summary_log.md` sono obbligatori da leggere ogni volta. 

Una volta finito l'LLM dovrà decidere se leggere o no anche i file `round_i.md` dei round precedenti.
Questo step è opzionale. Per ora l'idea che mi è venuta in mente per implementarlo è la seguente
- Una volta finito l'analisi di `summary_log` viene mandato un messaggio all'LLM chiedendogli se vuole leggere i file di log. La risposta deve essere semplicemente si o no.
- Se si gli si chiede che file vuole leggere (casomai gli si passa la lista con i nomi dei file). La risposta deve essere tassivamento un elenco dei file dei file da leggere.
- I file vengono caricati tutti insieme e passat all'LLM

Finita l'analisi dei round precedenti l'LLM dovrà aggiornare il file `round_i.md` del round corrente.
- Nella sezione `Summary Previous Rounds` dovrà mettere una riassunto molto breve di tutti i precedenti esperimenti (con eventuali riferimenti a a log precedenti nel caso servano dettagli)
- Nella sezione `Experiment Configuration Update` dovrà scrivere come vuole aggiornare i config dell'esperimento in questo round e perchè

# Aggiornamento file di config dell'esperimento
Una volta deciso come modificare i file dell'esperimento questi ultimi andranno aggiornati.
Penso che la funzione `modify_file` già implementata all'interno della backend possa bastare per questo compito.

Però voglio apportare delle piccole migliore al processo per renderlo più robusto.

I file di config sono banalmente dei dizionari. Prima di essere modificati voglio che `autoresearch` crei una copia di backup dei config.

Dopo la modifica dei dizionari tutte le key delle nuove versioni devono essere comparate con le key delle version di backup. 
Se ci sono delle discrepanze allora la modifica non è andata a buon fide e deve essere rifatta.

# Runnare l'esperimento

Questa parte è abbastanza semplice e consiste soltanto nel eseguire la funzione `run` che fa partire l'esperimento

# Analisi finale

Una volta ottenuti i risultati deve essere fatta un analisi su questo round dell'esperimento. 
Analisi e conclusioni devono essere salvati nella sezione `Result and analysis` dell'attuale file `round_i`.

# Sincronizzazione con la copia di backup interna al tool.

Una volta finito il round corrente tutti i risultati devono essere copiati nella cartella di backup internamente al tool.
Nota bene. Questo step deve essere l'ultima cosa che viene fatta.

Crea un funzione `sync` specificatamente per questo. 
Eventualmente aggiungi anche il comando da cli `jlt autoresearch sync` che prende i risultati dalla cartella dell'esperimento corrente e li copia nella cartella di backup interna al tool.
Questo comando deve avere due flag :
    - `--experiment_name`: nome con cui salvare l'esperimento. Se non specificato viene usato quella della cartella dove sono salvati i file.
    - `--reverse` : flag boolean opzionale. Se passata inverte il processo di sincronizzazione e i file all'interno della cartella di backup del tool vengono copiati in quella dell'esperimento













