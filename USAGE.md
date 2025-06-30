# Manuale d'Uso del Generatore di Prompt per LLM

Questo manuale descrive come utilizzare e estendere il sistema di generazione di prompt per LLM, progettato per produrre prompt ottimizzati che aderiscono alle best practice aziendali e utilizzano i migliori tool disponibili.

## 1. Struttura del Progetto

Il progetto è organizzato come segue:

-   `prompts/`: Contiene i template dei prompt.
    -   `base_prompts/`: Template generici (es. `generic_code_prompt.txt`).
    -   `language_specific/`: Template specifici per linguaggio (es. `python/feature_prompt.txt`).
    -   `framework_specific/`: Template specifici per framework (es. `react/component_prompt.txt`).
-   `knowledge_base/`: Memorizza informazioni dettagliate su best practice e tool.
    -   `best_practices/`: File Markdown (.md) con descrizioni delle best practice.
    -   `tools/`: File JSON (.json) con dettagli sui tool.
-   `config/`: File di configurazione.
    -   `tech_stack_mapping.json`: Mappa tecnologie a best practice e tool.
-   `src/`: Codice sorgente del generatore di prompt e del gestore della conoscenza.
    -   `prompt_generator.py`: Logica principale per l'assemblaggio dei prompt.
    -   `knowledge_manager.py`: Gestisce il caricamento e l'interrogazione della knowledge base.
    -   `utils.py`: Funzioni di utilità.
-   `main.py`: Script di esempio per la generazione di prompt.
-   `requirements.txt`: Dipendenze Python.
-   `venv/`: Ambiente virtuale Python (non versionato).

## 2. Installazione e Setup

1.  **Clona il repository** (se non l'hai già fatto):
    ```bash
    git clone <URL_DEL_REPOSITORY>
    cd <NOME_CARTELLA_PROGETTO>
    ```
2.  **Crea e attiva un ambiente virtuale**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Installa le dipendenze**:
    ```bash
    pip install -r requirements.txt
    ```

## 3. Utilizzo del Generatore di Prompt

Lo script `main.py` dimostra come utilizzare il `PromptGenerator`.

Per generare un prompt, esegui:

```bash
source venv/bin/activate && python3 main.py
```

Lo script `main.py` contiene esempi predefiniti che generano prompt per diverse combinazioni di tecnologie.

### Parametri di Generazione del Prompt

Il metodo `generate_prompt` in `src/prompt_generator.py` accetta i seguenti parametri:

-   `technologies` (list[str]): Una lista di stringhe che rappresentano le tecnologie (linguaggi, framework, tool) per cui generare il prompt (es. `["python", "docker", "ansible"]`).
-   `task_type` (str): Il tipo di compito da svolgere (es. "nuova funzionalità", "bug fix", "refactoring").
-   `task_description` (str): Una descrizione dettagliata del compito specifico (es. "un endpoint API per la registrazione utenti").
-   `code_requirements` (str): Requisiti specifici per il codice generato (es. "Il codice deve essere modulare, testabile e seguire i principi SOLID.").
-   `template_name` (str, opzionale): Il percorso del template di prompt da utilizzare, relativo alla directory `prompts/` (default: `base_prompts/generic_code_prompt.txt`).

### Esempio di Output

L'output sarà un prompt formattato che include la descrizione del compito, le best practice pertinenti con i loro dettagli e i tool raccomandati con le loro descrizioni e comandi di esempio.

```
--- Generated Prompt (Python Feature) ---
Come sviluppatore Python esperto, implementa la seguente funzionalità: un endpoint API per la registrazione utenti con validazione input e hashing password.

Assicurati di seguire le seguenti best practice:
### Clean Code Principles
# Clean Code Principles
...

Utilizza i seguenti tool per garantire la qualità del codice:
### Black
Description: Black is an uncompromising Python code formatter.
...

Il codice deve essere: Il codice deve essere modulare, testabile e seguire i principi SOLID. Utilizzare un ORM per l'interazione con il database.. Includi docstring e type hints appropriati.
-----------------------------------------
```

## 4. Estensione del Sistema

### A. Aggiungere Nuove Best Practice

1.  Crea un nuovo file Markdown (`.md`) in `knowledge_base/best_practices/`.
2.  Il nome del file (senza estensione) dovrebbe corrispondere al nome della best practice (es. `my_new_best_practice.md` per "My New Best Practice").
3.  Popola il file Markdown con una descrizione dettagliata della best practice.
4.  Aggiungi il nome della best practice al `tech_stack_mapping.json` sotto la tecnologia appropriata.

### B. Aggiungere Nuovi Tool

1.  Crea un nuovo file JSON (`.json`) in `knowledge_base/tools/`.
2.  Il nome del file (senza estensione) dovrebbe corrispondere al nome del tool (es. `my_new_tool.json` per "My New Tool").
3.  Popola il file JSON con i dettagli del tool (nome, descrizione, benefici, note d'uso, comando di esempio).
4.  Aggiungi il nome del tool al `tech_stack_mapping.json` sotto la tecnologia appropriata.

### C. Aggiungere Nuovi Template di Prompt

1.  Crea un nuovo file `.txt` in una delle sottocartelle di `prompts/` (es. `prompts/language_specific/java/my_java_template.txt`).
2.  Utilizza la sintassi Jinja2 per i placeholder (es. `{{ language }}`, `{{ best_practices }}`, `{{ tools }}`, `{{ task_description }}`, `{{ code_requirements }}`).
3.  Nel tuo script di utilizzo (es. `main.py`), specifica il `template_name` quando chiami `generate_prompt`.

### D. Aggiornare `config/tech_stack_mapping.json`

Questo file è il cuore della configurazione. Per ogni linguaggio, framework o tecnologia, puoi definire una lista di `best_practices` e `tools` associati. Assicurati che i nomi qui corrispondano ai nomi dei file (senza estensione) in `knowledge_base/best_practices/` e `knowledge_base/tools/`.

Esempio:

```json
{
    "python": {
        "best_practices": ["PEP8", "Clean Code Principles"],
        "tools": ["Pylint", "Black"]
    },
    "my_new_language": {
        "best_practices": ["My New Best Practice"],
        "tools": ["My New Tool"]
    }
}
```

## 5. Contribuzione

Sentiti libero di contribuire aggiungendo nuove best practice, tool, template o miglioramenti al codice. Apri una pull request con le tue modifiche.