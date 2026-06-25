Ciao Claude. 

Questa è una repo dove voglio sviluppare un pacchetto python chiamato Jesus's LLM Tools (JLT).
Come si può intuire dal nome saranno una serie di tool che useranno gli LLM.

Ho bisogno del tuo aiuto per finire il setup della repo.

Innanzitutto quando un tool verrà usato dovrà essere chiamato da `cli` con questa sintassi :
```
jlt <tool_name> <tool_subcommand, tool variable, tool flags>
```

Quindi `jlt` (l'acronimo di tutto questo progetto), `<tool_name>` il nome dello specifico tool e `<tool_input>` (ovvero tutti i possibili sottocomandi/input/flag dello specifico tool)

Ho già creato una struttura iniziale per la repo
```
  instructions/ ---> Folder with all the instructions for you
  scripts_sh/   ---> Folder for any shell scripts to be used in the future
  src/          ---> Folder for all the JLT source code
  tutorial/     ---> Old folder. You can ignore it
  LICENSE
󰂺  README.md
  pyproject.toml 
```

Dentro `src` c'è già la cartella `jlt`. Ogni tool poi dovrà avere una sua sottocartella internamente, e.g.
```
  src/
      jlt/
          tool_1/              ---> Source code for tool 1
          tool_2/              ---> Source code for tool 2
        ...
          tool_n/              ---> Source code for tool n
          shared_knowledge/    ---> Source code shared by all the tools
```

Ho bisogno che tu prepari la repo per lo sviluppo di due tool : `autoresearch` e `club`
