**Fase 0: Setup e Preparazione (Foundation)**

1.  **Setup Ambiente di Sviluppo:**
    *   Creare un ambiente virtuale Python (es. venv, conda).
    *   Installare le librerie necessarie: `streamlit`, `psycopg2-binary` (o `sqlalchemy` se si sceglie un ORM), `pandas` (utile per la gestione dei dati tabellari in Streamlit).
    *   Creare la struttura base del progetto (es. cartelle per `app`, `db`, `utils`, `tests`).
2.  **Configurazione Database:**
    *   Assicurarsi che il database PostgreSQL sia accessibile.
    *   Creare un file di configurazione (es. `.env`, `config.py`) per memorizzare in modo sicuro le credenziali del database (host, porta, utente, password, nome db). *Non committare le credenziali nel version control.*
    *   Implementare una funzione di utility (`db_utils.py` o simile) per stabilire e gestire la connessione al database (idealmente usando connection pooling con `psycopg2` o gestito dall'engine di SQLAlchemy). Gestire la chiusura corretta delle connessioni.
    *   *Opzionale ma Consigliato:* Configurare SQLAlchemy con i modelli corrispondenti alle tabelle del database fornite. Questo semplificherà notevolmente le query e le manipolazioni dei dati.
3.  **Struttura Applicazione Streamlit:**
    *   Creare il file principale dell'app Streamlit (es. `app.py`).
    *   Impostare la configurazione base della pagina Streamlit (`st.set_page_config`).
    *   Definire la struttura di navigazione principale (es. sidebar per le sezioni principali o tabs).

**Fase 1: Selezione Prodotto e Creazione Funnel Base (Core Workflow Initiation)**

4.  **Backend: Recupero Prodotti:**
    *   Implementare una funzione (es. `get_products()`) che si connetta al DB e recuperi l'elenco dei prodotti dalla tabella `product.products` (almeno `id`, `product_code`, `product_description`, `title_prod`).
5.  **UI: Selezione Prodotto:**
    *   Nell'app Streamlit, utilizzare `st.selectbox` o un widget simile per mostrare l'elenco dei prodotti recuperati.
    *   Implementare una funzionalità di ricerca/filtro se l'elenco è lungo (si può usare `st.text_input` per filtrare la lista dei prodotti prima di mostrarla nel selectbox, o esplorare componenti custom se necessario).
    *   Memorizzare l'`id` del prodotto selezionato nello stato della sessione di Streamlit (`st.session_state`).
6.  **Backend: Creazione Funnel Automatizzata:**
    *   Implementare una funzione (es. `create_product_funnel(product_id, product_name, default_broker_id)`).
    *   Questa funzione deve:
        *   Connettersi al DB.
        *   Iniziare una transazione.
        *   Creare un record in `funnel_manager.workflow` con una descrizione tipo f"Workflow per {product_name}". Recuperare l'ID del workflow creato.
        *   Creare un record in `funnel_manager.funnel` associando `workflow_id`, `product_id`, e un `broker_id` di default (questo ID di default deve essere configurabile, magari letto da un file di configurazione o da una variabile d'ambiente). Il nome del funnel potrebbe essere tipo f"Funnel - {product_name}".
        *   Eseguire il commit della transazione.
        *   Restituire l'ID del funnel creato (o un oggetto rappresentante il funnel).
        *   Gestire potenziali errori (es. prodotto già associato a un funnel, errori DB) e restituire feedback appropriato.
7.  **UI: Pulsante Creazione Funnel:**
    *   Visualizzare un pulsante `st.button("Crea Funnel per Prodotto selezionato")` *solo* dopo che un prodotto è stato selezionato.
    *   Al click del pulsante:
        *   Chiamare la funzione `create_product_funnel` passando l'ID del prodotto selezionato e il nome.
        *   Mostrare un messaggio di successo (`st.success`) con l'ID o nome del funnel creato, o un messaggio di errore (`st.error`) in caso di fallimento.
        *   Memorizzare l'ID del funnel e del workflow associati nello `st.session_state` per le fasi successive.
8.  **UI: Visualizzazione Funnel Esistente (Opzionale ma Utile):**
    *   Dopo la selezione del prodotto, controllare se esiste già un funnel associato a quel `product_id`. Se esiste, mostrare le informazioni base del funnel e passare direttamente alla gestione degli step, invece di mostrare il pulsante "Crea".

**Fase 2: Gestione Step del Funnel (Building Blocks)**

9.  **Backend: Operazioni CRUD per Step:**
    *   Implementare funzioni per:
        *   `create_step(step_url, shopping_cart=None, post_message=False, step_code=None, gtm_reference=None)`: Inserisce un nuovo record in `funnel_manager.step`. Include validazione per l'univocità di `step_url`.
        *   `get_steps()`: Recupera tutti gli step esistenti (potrebbe essere necessario filtrare per quelli non ancora associati a *questo* workflow/funnel per la selezione).
        *   `get_steps_for_workflow(workflow_id)`: Recupera gli step già associati alle route di un dato workflow (utile per la visualizzazione).
        *   `update_step(...)`: (Potrebbe non essere strettamente MVP, ma utile).
        *   `delete_step(...)`: (Considerare le implicazioni sulle route esistenti).
10. **UI: Sezione Gestione Step:**
    *   Creare una sezione dedicata (es. un `st.expander` o una tab) visibile *solo* dopo che un funnel è stato selezionato o creato.
    *   **Creazione Nuovo Step:**
        *   Usare `st.text_input` per `step_url`. Implementare validazione in tempo reale (on_change) per controllare l'univocità rispetto agli step esistenti nel DB e suggerire formati validi (usare regex semplice). Mostrare un avviso (`st.warning`) se l'URL esiste già.
        *   Usare `st.text_area` o un componente specifico (se ne esistono per Streamlit, come `streamlit-ace`) per l'input JSON di `shopping_cart` e `gtm_reference`. Aggiungere placeholder/esempi e un link a un validatore JSON online o una semplice validazione `json.loads()` in Python con feedback.
        *   Usare `st.checkbox` per `post_message` con `help="Spiega qui cosa fa post_message..."`.
        *   Usare `st.text_input` per `step_code` (opzionale) con `help="Codice identificativo interno o per tracking."`.
        *   Pulsante `st.button("Crea Step")` che chiama `create_step` e aggiorna la UI. Fornire feedback (`st.success`/`st.error`).
    *   **Selezione Step Esistente (per aggiungerlo al Funnel):**
        *   *Questo concetto si fonde meglio con la creazione delle Route (Fase 3).* Invece di "selezionare uno step esistente" genericamente, l'utente selezionerà step esistenti *quando crea una route*.
    *   **Visualizzazione Step del Funnel:**
        *   Mostrare una tabella o lista (`st.dataframe` o iterazione con `st.write`/`st.metric`) degli step *attualmente collegati* tramite le route al `workflow_id` del funnel corrente (recuperati tramite `get_steps_for_workflow` o analizzando le route). Visualizzare colonne chiave come `step_url`, `step_code`.

**Fase 3: Definizione delle Route (Connecting the Blocks)**

11. **Backend: Operazioni CRUD per Route:**
    *   Implementare funzioni per:
        *   `create_route(workflow_id, from_step_id, next_step_id, route_config=None)`: Inserisce un nuovo record in `funnel_manager.route`. Assicurarsi che `next_step_id` esista. `from_step_id` può essere null nel caso di primo step
        *   `get_routes_for_workflow(workflow_id)`: Recupera tutte le route associate a un workflow.
        *   `delete_route(route_id)`: Elimina una route.
12. **UI: Gestione Route:**
    *   All'interno della sezione Gestione Step, o in una sezione dedicata "Collegamenti / Route".
    *   **Creazione Route:**
        *   Recuperare *tutti* gli step disponibili (`get_steps()`) per popolare i selectbox.
        *   Usare due `st.selectbox`, "Route DA Step:", popolato con gli step, e "Route A Step:", popolato anch'esso con gli step. Filtrare magari per non permettere route da uno step a se stesso, se non desiderato. Associare gli `id` degli step selezionati.
        *   *Alternativa/Aggiunta Visuale:* Esplorare `streamlit-agraph` o simili per una visualizzazione a grafo *semplice* degli step e permettere la creazione di link (potrebbe essere post-MVP).
        *   *Opzionale:* Input per `route_config` (JSON editor come per gli step).
        *   Pulsante `st.button("Crea Collegamento (Route)")` che chiama `create_route` con `workflow_id` (da `st.session_state`), `from_step_id`, `next_step_id`. Fornire feedback e aggiornare la visualizzazione delle route.
    *   **Visualizzazione Route:**
        *   Mostrare una tabella (`st.dataframe`) o una lista delle route esistenti per il workflow corrente (recuperate con `get_routes_for_workflow`), mostrando "Da Step URL/Code" -> "A Step URL/Code".
        *   Aggiungere un pulsante "Elimina" per ogni route che chiama `delete_route`.

**Fase 4: Configurazione UI per Step (Sections & Components)**

13. **Backend: Operazioni CRUD per Design Entities:**
    *   Implementare funzioni per interagire con le tabelle `design.section`, `design.component`, `design.step_section`, `design.component_section`, `design.structure`, `design.structure_component_section`, `design.cms_key`. Queste funzioni gestiranno la creazione, l'associazione (tramite tabelle ponte come `step_section`, `component_section`), il recupero e l'ordinamento.
    *   `create_section(sectiontype)`
    *   `get_sections()`
    *   `create_component(component_type)`
    *   `get_components()`
    *   `add_section_to_step(step_id, section_id, order, product_id=None, broker_id=None)`: Crea record in `design.step_section`.
    *   `get_sections_for_step(step_id, product_id=None, broker_id=None)`: Recupera le sezioni associate a uno step, ordinate per `order`.
    *   `update_step_section_order(step_section_id, new_order)` (o un modo per riordinare tutte le sezioni di uno step).
    *   `add_component_to_section(section_id, component_id, order)`: Crea record in `design.component_section`.
    *   `get_components_for_section(section_id)`: Recupera i componenti associati a una sezione, ordinati per `order`.
    *   `update_component_section_order(...)`
    *   `create_structure_for_component_section(component_section_id, structure_data)`: Crea record in `design.structure` e `design.structure_component_section` (con structure vuota inizialmente, poi aggiornata).
    *   `update_structure_data(structure_id, new_data)`
    *   `get_structure_for_component_section(component_section_id)`
    *   `create_or_update_cms_key(structure_component_section_id, cms_data)`: Crea/aggiorna record in `design.cms_key`.
    *   `get_cms_key_for_structure(...)`
14. **UI: Configurazione UI per Step Selezionato:**
    *   Quando uno step viene selezionato dalla lista/grafo (nella Fase 2/3), mostrare una nuova area di configurazione UI per *quello* step. Usare `st.session_state` per tracciare lo step attualmente selezionato per la configurazione UI.
    *   **Gestione Sezioni:**
        *   Mostrare le sezioni già associate allo step (ottenute con `get_sections_for_step`), ordinate. Usare `st.expander` per ogni sezione associata.
        *   Permettere il riordinamento (idealmente drag-and-drop se si trova una libreria Streamlit adatta, altrimenti con pulsanti "Su"/"Giù" che chiamano `update_step_section_order`).
        *   **Aggiungi Sezione:**
            *   `st.selectbox("Seleziona Sezione Esistente", options=get_sections(), format_func=lambda s: s.sectiontype)` O
            *   `st.text_input("Crea Nuova Sezione (Tipo)", placeholder="Es. Header, Body, Footer")`
            *   Pulsante `st.button("Aggiungi/Crea e Aggiungi Sezione allo Step")` che chiama `create_section` (se necessario) e poi `add_section_to_step` (calcolando il prossimo `order`). Aggiornare la lista di sezioni.
    *   **Gestione Componenti (all'interno dell'expander di ogni Sezione):**
        *   Mostrare i componenti già associati alla sezione (ottenuti con `get_components_for_section`), ordinati. Usare `st.expander` o un layout simile per ogni componente.
        *   Permettere il riordinamento (come per le sezioni).
        *   **Aggiungi Componente:**
            *   `st.selectbox("Seleziona Componente Esistente", options=get_components(), format_func=lambda c: c.component_type)` O
            *   `st.text_input("Crea Nuovo Componente (Tipo)", placeholder="Es. Banner, Form, Video")`
            *   Pulsante `st.button("Aggiungi/Crea e Aggiungi Componente alla Sezione")` che chiama `create_component` (se necessario) e poi `add_component_to_section` (calcolando il prossimo `order`). Questo dovrebbe anche creare automaticamente i record collegati `design.structure` (vuoto) e `design.structure_component_section`. Aggiornare la lista dei componenti.
    *   **Configurazione Dati Componente (all'interno dell'area di ogni Componente):**
        *   **Structure Data:**
            *   Recuperare `structure_id` da `design.structure_component_section` e poi i dati da `design.structure`.
            *   Usare `st.text_area` (o editor JSON migliore) per visualizzare/modificare `design.structure.data`. Aggiungere validazione JSON `on_change`.
            *   Pulsante `st.button("Salva Dati Struttura")` che chiama `update_structure_data`.
        *   **CMS Keys:**
            *   Recuperare `structure_component_section_id`.
            *   Recuperare i dati da `design.cms_key` associati.
            *   Usare `st.text_area` (o editor JSON) per visualizzare/modificare `design.cms_key.value` (assicurandosi sia un JSON chiave-valore valido).
            *   Pulsante `st.button("Salva CMS Keys")` che chiama `create_or_update_cms_key`.

**Fase 5: Visualizzazione e Feedback**

15. **Implementazione Feedback Utente:**
    *   Utilizzare `st.success`, `st.error`, `st.warning`, `st.info` in modo consistente dopo ogni operazione utente (creazione, aggiornamento, eliminazione).
    *   Usare `st.spinner` durante le operazioni di backend potenzialmente lunghe.
16. **Visualizzazione Riepilogativa:**
    *   Considerare un pannello di riepilogo (magari nella sidebar o in una tab dedicata) che mostri:
        *   Prodotto selezionato.
        *   Funnel/Workflow associato.
        *   Lista degli step nel funnel (con URL/Code).
        *   Visualizzazione (anche testuale) delle route definite (Es. StepA -> StepB).
        *   *Avanzato:* Una visualizzazione grafica semplice (es. usando `st.graphviz_chart` o `streamlit-agraph`) del flusso degli step e delle route.
    *   Assicurarsi che le liste di step, sezioni, componenti siano chiare e mostrino le informazioni identificative principali.

**Fase 6: Testing, Documentazione e Deployment Prep**

17. **Testing:**
    *   Scrivere test unitari per le funzioni di backend (specialmente quelle che interagiscono col DB). Usare `pytest` e possibilmente mocking per isolare le dipendenze DB.
    *   Eseguire test manuali approfonditi dell'interfaccia Streamlit, coprendo tutti i flussi utente MVP.
18. **Documentazione:**
    *   Aggiungere docstring alle funzioni Python.
    *   Creare un file `README.md` con istruzioni per setup, configurazione e avvio.
    *   Scrivere una breve guida utente (può essere un file Markdown o una pagina nell'app Streamlit stessa usando `st.markdown`) che spieghi il flusso di lavoro: selezione prodotto -> creazione funnel -> aggiunta step -> collegamento route -> configurazione UI step.
    *   Utilizzare `st.help` o `st.caption` all'interno dell'app per fornire spiegazioni contestuali per campi o sezioni complesse.
19. **Deployment Prep:**
    *   Creare un `requirements.txt` finale.
    *   Considerare la containerizzazione con Docker (creare un `Dockerfile`).
    *   Documentare i passi necessari per il deployment (configurazione variabili d'ambiente, avvio dell'app).

**Iterazione e Miglioramento (Post-MVP)**

*   Raccogliere feedback dagli utenti target.
*   Iterare sull'UI/UX basandosi sul feedback.
*   Implementare gradualmente le "Funzionalità Avanzate" prioritarie (es. validazione più robusta, drag-and-drop se fattibile, anteprima UI).
*   Monitorare le metriche di successo definite.

Questa sequenza fornisce una roadmap dettagliata per costruire l'MVP, mettendo la user experience e l'automazione al centro del processo. Ricorda di lavorare in modo iterativo, testando frequentemente e adattando il piano se necessario.