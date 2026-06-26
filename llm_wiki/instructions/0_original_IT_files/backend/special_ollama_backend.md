OBSOLETO. Penso di poter ottenere la stessa cosa sfruttando `OLLAMA_KEEP_ALIVE`


Voglio creare una versione speciale della backend di Ollama, una sua estensione.

Verrà usata principalmente con il tool di autoresearch (anche se non escludo la possibilità che in futuro possa usarla anche per altro).

Questa backend deve essere usata per sistemi che non hanno abbastanza memoria per tenere attivo allo stesso tempo un server di ollama ed eseguire il l'autoresearch quando è richiesta una GPU.
Scenario che mi sto immaginando
- Voglio addestrare una rete neurale abbastanza grande
- Voglio usare autoresearch per fare un'ottimizzazione degli iperparametri
- Come backend ho impostato ollama ma uso un modello molto grande perchè voglio più capacità di reasoning
- La GPU non riesce a tenere in memoria allo stesso tempo il server di Ollama e fare il training

La soluzione? Creare al momento il server di ollama e poi distruggerlo quando ha finito il task. O se non distruggerlo quantomeno rimuovere il modello dalla memoria
Quindi questa backend deve funzionare in maniera analoga a quella di ollama ma con un extra. Si deve occupare lei di creare e distruggere il server.
E' letteralmente costruita per ricevere ed eseguire un solo comando.
