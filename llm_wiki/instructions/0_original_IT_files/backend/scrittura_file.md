# Scrittura di file

Mentre scrivevo le istruzioni per eseguire l'esperimento mi sono reso conto che sarebbe stato comodo avere una funzione per creare dei file di testo internamente a questo pacchetto.
L'idea che mi è venuta in mente è la seguente.

Funzione generica `write_file(text : str, extension : str = 'txt')` che crea un file con il testo dato in input e l'estensione specificata.
Le possibili estensioni per ora sono solo `txt` e `md`. Se non specificata va di default su `txt`
Nel caso tu lo ritenga opportuno puoi decidere un altro nome se pensi che faccia meno confusione o sia più adatto.

Una funzione interna alle backend usata dagli LLM per scrivere file.
E.g. Ho necessità di aggiornare un file di config di un esperimento per il tool di autoreseach. Quindi l'LLM dovrà essere capace di leggere e modificare un file in base a quanto gli è stato richiesto.

Una volta finito aggiorna eventuali file nella wiki.
