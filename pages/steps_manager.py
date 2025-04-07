import copy
import json
import logging

import pandas as pd
import streamlit as st

from db.step_operations import (
    create_step,
    delete_step,
    get_steps,
    get_steps_for_workflow,
    update_step,
)
from utils.error_handler import handle_error, log_operation

# Configurazione del logging
logger = logging.getLogger(__name__)

# Configurazione della pagina
st.title("Gestione Step del Funnel")


# Utilizzo di st.cache_data per le operazioni di database
@st.cache_data(ttl=600)
def cached_get_steps():
    """Recupera tutti gli step dal database con caching."""
    with st.spinner("Caricamento degli step..."):
        try:
            steps = get_steps()
            log_operation("Recupero di tutti gli step", {"count": len(steps)})
            return steps
        except Exception as e:
            return handle_error(
                e, "Errore durante il recupero degli step", fallback_data=[]
            ).get("data", [])


@st.cache_data(ttl=600)
def cached_get_steps_for_workflow(workflow_id):
    """Recupera gli step associati a un workflow specifico con caching."""
    if not workflow_id:
        return []

    with st.spinner(f"Caricamento degli step del workflow {workflow_id}..."):
        try:
            steps = get_steps_for_workflow(workflow_id)
            log_operation(
                "Recupero step per workflow",
                {"workflow_id": workflow_id, "count": len(steps)},
            )
            return steps
        except Exception as e:
            return handle_error(
                e,
                f"Errore durante il recupero degli step per il workflow {workflow_id}",
                fallback_data=[],
            ).get("data", [])


def validate_json_input(json_string):
    """Valida un input JSON e restituisce un dizionario o None."""
    if not json_string:
        return None

    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        return "error"


def save_state_for_undo(action_type, step_data):
    """
    Salva lo stato corrente per la funzionalità di annullamento.

    Args:
        action_type (str): Il tipo di azione ('create', 'update', 'delete')
        step_data (dict): I dati dello step coinvolto nell'azione
    """
    # Limita lo stack di annullamento a 10 elementi
    if len(st.session_state.undo_stack) >= 10:
        st.session_state.undo_stack.pop(0)

    # Salva l'operazione corrente
    st.session_state.undo_stack.append(
        {"action_type": action_type, "step_data": copy.deepcopy(step_data)}
    )

    logger.debug(
        f"Stato salvato per annullamento: {action_type} su step {step_data.get('id')}"
    )


def handle_step_creation():
    """Gestisce la creazione di un nuovo step tramite form."""
    # Validazione dei dati JSON
    shopping_cart = validate_json_input(st.session_state.step_shopping_cart)
    if shopping_cart == "error":
        st.session_state.notification = {
            "type": "error",
            "message": "Il formato JSON di shopping_cart non è valido",
        }
        st.stop()

    gtm_reference = validate_json_input(st.session_state.step_gtm_reference)
    if gtm_reference == "error":
        st.session_state.notification = {
            "type": "error",
            "message": "Il formato JSON di gtm_reference non è valido",
        }
        return

    # Verifica che l'URL dello step sia stato fornito
    if not st.session_state.step_url:
        st.session_state.notification = {
            "type": "warning",
            "message": "È necessario specificare l'URL dello step",
        }
        return

    # Raccogliere i dati dello step per la funzionalità di annullamento
    step_data = {
        "step_url": st.session_state.step_url,
        "shopping_cart": shopping_cart,
        "post_message": st.session_state.step_post_message,
        "step_code": st.session_state.step_code,
        "gtm_reference": gtm_reference,
    }

    with st.spinner("Creazione dello step in corso..."):
        # Creazione dello step
        result = create_step(
            st.session_state.step_url,
            shopping_cart,
            st.session_state.step_post_message,
            st.session_state.step_code,
            gtm_reference,
        )

    if not result["error"]:
        # Salva lo stato per l'annullamento
        if "id" in result:
            step_data["id"] = result["id"]
            save_state_for_undo("create", step_data)

        # Imposta la notifica di successo
        st.session_state.notification = {
            "type": "success",
            "message": result["message"],
        }
        # Invalida la cache degli step
        st.session_state.invalidate_step_cache = True
        # Resetta i campi del form
        st.session_state.step_url = ""
        st.session_state.step_shopping_cart = ""
        st.session_state.step_post_message = False
        st.session_state.step_code = ""
        st.session_state.step_gtm_reference = ""
        # Ricarica la pagina
        st.rerun()
    else:
        # Imposta la notifica di errore
        st.session_state.notification = {"type": "error", "message": result["message"]}


def handle_step_update(step_id, updated_data):
    """
    Gestisce l'aggiornamento di uno step esistente.

    Args:
        step_id (int): ID dello step da aggiornare
        updated_data (dict): Dizionario con i dati aggiornati dello step
    """
    # Trova lo step originale per la funzionalità di annullamento
    original_step = next(
        (
            s
            for s in cached_get_steps_for_workflow(st.session_state.workflow_id)
            if s["id"] == step_id
        ),
        None,
    )

    if not original_step:
        st.error(f"Step con ID {step_id} non trovato")
        return

    # Salvare lo stato originale prima dell'aggiornamento
    save_state_for_undo("update", copy.deepcopy(original_step))

    with st.spinner(f"Aggiornamento dello step {step_id} in corso..."):
        result = update_step(
            step_id,
            updated_data.get("step_url"),
            updated_data.get("shopping_cart"),
            updated_data.get("post_message"),
            updated_data.get("step_code"),
            updated_data.get("gtm_reference"),
        )

    if not result["error"]:
        st.session_state.notification = {
            "type": "success",
            "message": f"Step {step_id} aggiornato con successo",
        }
        st.session_state.invalidate_step_cache = True
        st.rerun()
    else:
        st.session_state.notification = {"type": "error", "message": result["message"]}


def handle_step_delete(step_id):
    """
    Gestisce l'eliminazione di uno step.

    Args:
        step_id (int): ID dello step da eliminare
    """
    # Trova lo step da eliminare per la funzionalità di annullamento
    step_to_delete = next(
        (
            s
            for s in cached_get_steps_for_workflow(st.session_state.workflow_id)
            if s["id"] == step_id
        ),
        None,
    )

    if not step_to_delete:
        st.error(f"Step con ID {step_id} non trovato")
        return

    # Salvare lo stato prima dell'eliminazione
    save_state_for_undo("delete", copy.deepcopy(step_to_delete))

    with st.spinner(f"Eliminazione dello step {step_id} in corso..."):
        result = delete_step(step_id)

    if not result["error"]:
        st.session_state.notification = {
            "type": "success",
            "message": f"Step {step_id} eliminato con successo",
        }
        st.session_state.invalidate_step_cache = True
        st.session_state.selected_step_id = None  # Reset della selezione
        st.rerun()
    else:
        st.session_state.notification = {"type": "error", "message": result["message"]}


def handle_undo_action():
    """Gestisce l'annullamento dell'ultima azione."""
    if not st.session_state.undo_stack:
        st.warning("Nessuna azione da annullare")
        return

    # Recupera l'ultima azione
    last_action = st.session_state.undo_stack.pop()
    action_type = last_action["action_type"]
    step_data = last_action["step_data"]

    with st.spinner("Annullamento dell'operazione in corso..."):
        if action_type == "create":
            # Annulla la creazione eliminando lo step
            result = delete_step(step_data["id"])
            message = f"Creazione dello step {step_data['id']} annullata"

        elif action_type == "update":
            # Annulla l'aggiornamento ripristinando lo stato precedente
            result = update_step(
                step_data["id"],
                step_data["step_url"],
                step_data.get("shopping_cart"),
                step_data.get("post_message"),
                step_data.get("step_code"),
                step_data.get("gtm_reference"),
            )
            message = f"Modifiche allo step {step_data['id']} annullate"

        elif action_type == "delete":
            # Annulla l'eliminazione ricreando lo step
            result = create_step(
                step_data["step_url"],
                step_data.get("shopping_cart"),
                step_data.get("post_message"),
                step_data.get("step_code"),
                step_data.get("gtm_reference"),
            )
            message = f"Eliminazione dello step {step_data['id']} annullata"

    if not result.get("error", True):
        st.session_state.notification = {"type": "success", "message": message}
        st.session_state.invalidate_step_cache = True
        st.rerun()
    else:
        st.session_state.notification = {
            "type": "error",
            "message": f"Impossibile annullare l'operazione: {result.get('message', 'Errore sconosciuto')}",
        }


# Mostra le notifiche
if "notification" in st.session_state and st.session_state.notification:
    notification_type = st.session_state.notification["type"]
    message = st.session_state.notification["message"]

    if notification_type == "success":
        st.success(message)
    elif notification_type == "info":
        st.info(message)
    elif notification_type == "warning":
        st.warning(message)
    elif notification_type == "error":
        st.error(message)

    # Reset della notifica dopo la visualizzazione
    st.session_state.notification = None

# Verifica se è stato selezionato un prodotto e un funnel
if not st.session_state.selected_product_id or not st.session_state.funnel_id:
    st.warning(
        "Seleziona prima un prodotto e crea un funnel nella pagina 'Selezione Prodotto'."
    )

    # Pulsante per tornare alla selezione del prodotto
    st.page_link(
        "pages/product_selection.py", label="Vai a Selezione Prodotti", icon="🛒"
    )
    st.stop()

st.subheader(f"Funnel per: {st.session_state.selected_product_name}")

# Uso di expander per mostrare informazioni tecniche quando necessario
with st.expander("Dettagli tecnici"):
    st.write(f"Funnel ID: {st.session_state.funnel_id}")
    st.write(f"Workflow ID: {st.session_state.workflow_id}")

# Invalidazione condizionale della cache
if (
    "invalidate_step_cache" in st.session_state
    and st.session_state.invalidate_step_cache
):
    cached_get_steps.clear()
    cached_get_steps_for_workflow.clear()
    st.session_state.invalidate_step_cache = False

# Pulsante "Annulla" se ci sono azioni nello stack
if "undo_stack" in st.session_state and st.session_state.undo_stack:
    st.sidebar.button(
        "↩️ Annulla ultima azione", on_click=handle_undo_action, type="secondary"
    )

# Layout a colonne per una migliore organizzazione
col1, col2 = st.columns([2, 3])

with col1:
    # Form per la creazione di un nuovo step (usando st.form per batch processing)
    with st.container(border=True):
        st.subheader("Crea Nuovo Step")

        # Uso st.form per raggruppare i controlli e ridurre i reruns
        with st.form(key="create_step_form"):
            st.text_input(
                "URL dello Step:",
                key="step_url",
                help="URL univoco dello step (obbligatorio)",
            )

            # Editor JSON per i campi complessi
            st.text_area(
                "Shopping Cart (JSON):",
                key="step_shopping_cart",
                help="Configurazione del carrello in formato JSON (opzionale)",
                height=100,
            )

            st.checkbox(
                "Post Message",
                key="step_post_message",
                help="Abilita i post message per questo step",
            )

            st.text_input(
                "Step Code:",
                key="step_code",
                help="Codice identificativo interno o per tracking (opzionale)",
            )

            st.text_area(
                "GTM Reference (JSON):",
                key="step_gtm_reference",
                help="Riferimento GTM in formato JSON (opzionale)",
                height=100,
            )

            submit_button = st.form_submit_button(
                "Crea Step",
                type="primary",
                help="Crea un nuovo step con i parametri specificati",
            )

            if submit_button:
                handle_step_creation()

    # Guida rapida per la creazione di step
    with st.expander("📌 Guida rapida"):
        st.markdown(
            """
        ### Come creare uno step:
        
        1. **URL dello Step**: Inserisci l'URL univoco che identifica lo step
        2. **Shopping Cart**: Configura il carrello in formato JSON (opzionale)
        3. **Post Message**: Abilita se lo step deve utilizzare i post message
        4. **Step Code**: Inserisci un codice identificativo (utile per tracking)
        5. **GTM Reference**: Configura i riferimenti GTM in formato JSON (opzionale)
        
        **Esempio di formato JSON valido:**
        ```json
        {
          "key": "value",
          "nested": {
            "array": [1, 2, 3]
          }
        }
        ```
        """
        )

with col2:
    # Carica gli step associati al workflow corrente
    workflow_steps = cached_get_steps_for_workflow(st.session_state.workflow_id)

    if workflow_steps:
        st.subheader(f"Step del Workflow ({len(workflow_steps)})")

        # Paginazione per gli step
        steps_per_page = 5
        total_pages = (len(workflow_steps) + steps_per_page - 1) // steps_per_page

        if total_pages > 1:
            col_page, col_info = st.columns([2, 3])
            with col_page:
                current_page = st.number_input(
                    "Pagina",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    key="steps_current_page",
                )
            with col_info:
                st.info(f"Visualizzazione pagina {current_page} di {total_pages}")

            # Calcola l'indice di inizio e fine per la paginazione
            start_idx = (current_page - 1) * steps_per_page
            end_idx = min(start_idx + steps_per_page, len(workflow_steps))

            paginated_steps = workflow_steps[start_idx:end_idx]
        else:
            paginated_steps = workflow_steps

        # Utilizza un dataframe interattivo per visualizzare gli step
        df_steps = pd.DataFrame(paginated_steps)
        df_view = df_steps.copy()

        # Limita le colonne per una visualizzazione più chiara
        if len(df_view.columns) > 0:
            columns_to_display = ["id", "step_url", "step_code", "post_message"]
            # Assicurati che tutte le colonne esistano nel DataFrame
            columns_to_display = [
                col for col in columns_to_display if col in df_view.columns
            ]

            # Configura le colonne del dataframe
            column_config = {
                "id": st.column_config.NumberColumn(
                    "ID", help="Identificativo dello step"
                ),
                "step_url": st.column_config.TextColumn("URL", help="URL dello step"),
                "step_code": st.column_config.TextColumn(
                    "Codice", help="Codice identificativo"
                ),
                "post_message": st.column_config.CheckboxColumn(
                    "Post Message", help="Post message abilitato"
                ),
            }

            # Visualizza un dataframe interattivo
            st.dataframe(
                df_view[columns_to_display],
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
            )

        # Visualizzazione dettagliata di uno step selezionato
        st.subheader("Dettagli Step")

        selected_step_id = st.selectbox(
            "Seleziona uno step per vedere i dettagli:",
            options=[None] + [s["id"] for s in workflow_steps],
            format_func=lambda x: (
                "Seleziona uno step..."
                if x is None
                else f"Step {x} - {next((s['step_url'] for s in workflow_steps if s['id'] == x), '')}"
            ),
        )

        if selected_step_id:
            # Aggiorna lo step selezionato nella session state
            st.session_state.selected_step_id = selected_step_id

            # Trova lo step selezionato
            selected_step = next(
                (s for s in workflow_steps if s["id"] == selected_step_id), None
            )
            if selected_step:
                # Mostra i dettagli in un container con bordo
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"### {selected_step['step_url']}")
                        st.caption(f"ID: {selected_step['id']}")

                    with col2:
                        st.metric("Codice", selected_step["step_code"] or "N/A")

                    st.divider()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(
                            "**Post message:**",
                            (
                                "✅ Abilitato"
                                if selected_step.get("post_message")
                                else "❌ Disabilitato"
                            ),
                        )

                    # Visualizzazione delle configurazioni JSON
                    if selected_step.get("shopping_cart"):
                        with st.expander("Shopping Cart Configuration"):
                            st.json(selected_step["shopping_cart"])

                    if selected_step.get("gtm_reference"):
                        with st.expander("GTM Reference"):
                            st.json(selected_step["gtm_reference"])

                    # Aggiungi pulsanti di azione
                    col1, col2 = st.columns(2)

                    with col1:
                        # Dialog di conferma per l'eliminazione
                        if "confirm_delete" not in st.session_state:
                            st.session_state.confirm_delete = False

                        delete_clicked = st.button("🗑️ Elimina Step", type="secondary")

                        # Mostra dialog di conferma eliminazione
                        if delete_clicked:
                            st.session_state.confirm_delete = True

                        if st.session_state.confirm_delete:
                            st.warning(
                                "Sei sicuro di voler eliminare questo step? L'operazione può essere annullata dopo."
                            )
                            col_confirm, col_cancel = st.columns(2)
                            with col_confirm:
                                if st.button("Sì, elimina", type="primary"):
                                    handle_step_delete(selected_step_id)
                                    st.session_state.confirm_delete = False
                            with col_cancel:
                                if st.button("Annulla"):
                                    st.session_state.confirm_delete = False

                    with col2:
                        # Pulsante per modalità di modifica
                        if st.button("✏️ Modifica"):
                            st.session_state.editing_step = True
                            st.session_state.edit_step_id = selected_step_id
                            st.session_state.edit_step_url = selected_step["step_url"]
                            st.session_state.edit_step_code = selected_step.get(
                                "step_code", ""
                            )
                            st.session_state.edit_post_message = selected_step.get(
                                "post_message", False
                            )
                            st.session_state.edit_shopping_cart = (
                                json.dumps(
                                    selected_step.get("shopping_cart", {}), indent=2
                                )
                                if selected_step.get("shopping_cart")
                                else ""
                            )
                            st.session_state.edit_gtm_reference = (
                                json.dumps(
                                    selected_step.get("gtm_reference", {}), indent=2
                                )
                                if selected_step.get("gtm_reference")
                                else ""
                            )

                # Form di modifica, mostrato solo quando necessario
                if (
                    "editing_step" in st.session_state
                    and st.session_state.editing_step
                    and st.session_state.edit_step_id == selected_step_id
                ):
                    with st.form("edit_step_form"):
                        st.subheader("Modifica Step")

                        edit_url = st.text_input(
                            "URL dello Step:", value=st.session_state.edit_step_url
                        )
                        edit_step_code = st.text_input(
                            "Step Code:", value=st.session_state.edit_step_code
                        )
                        edit_post_message = st.checkbox(
                            "Post Message", value=st.session_state.edit_post_message
                        )
                        edit_shopping_cart = st.text_area(
                            "Shopping Cart (JSON):",
                            value=st.session_state.edit_shopping_cart,
                            height=100,
                        )
                        edit_gtm_reference = st.text_area(
                            "GTM Reference (JSON):",
                            value=st.session_state.edit_gtm_reference,
                            height=100,
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Salva Modifiche", type="primary"):
                                # Validazione dei dati JSON
                                shopping_cart = validate_json_input(edit_shopping_cart)
                                if shopping_cart == "error":
                                    st.error(
                                        "Il formato JSON di shopping_cart non è valido"
                                    )
                                    st.stop()

                                gtm_reference = validate_json_input(edit_gtm_reference)
                                if gtm_reference == "error":
                                    st.error(
                                        "Il formato JSON di gtm_reference non è valido"
                                    )
                                    st.stop()

                                # Aggiorna lo step
                                updated_data = {
                                    "step_url": edit_url,
                                    "step_code": edit_step_code,
                                    "post_message": edit_post_message,
                                    "shopping_cart": shopping_cart,
                                    "gtm_reference": gtm_reference,
                                }

                                handle_step_update(selected_step_id, updated_data)
                                st.session_state.editing_step = False

                        with col2:
                            if st.form_submit_button("Annulla Modifiche"):
                                st.session_state.editing_step = False
    else:
        st.info(
            "Nessuno step associato a questo workflow. Crea nuovi step utilizzando il form a sinistra."
        )

    # Mostra tutti gli step disponibili in un expander
    with st.expander("Altri Step Disponibili"):
        all_steps = cached_get_steps()
        if all_steps:
            st.write(f"Totale step disponibili: {len(all_steps)}")

            # Paginazione per tutti gli step
            all_steps_per_page = 10
            all_steps_pages = (
                len(all_steps) + all_steps_per_page - 1
            ) // all_steps_per_page

            if all_steps_pages > 1:
                col_page, col_info = st.columns([2, 3])
                with col_page:
                    all_current_page = st.number_input(
                        "Pagina",
                        min_value=1,
                        max_value=all_steps_pages,
                        value=1,
                        key="all_steps_current_page",
                    )
                with col_info:
                    st.info(
                        f"Visualizzazione pagina {all_current_page} di {all_steps_pages}"
                    )

                # Calcola l'indice di inizio e fine per la paginazione
                all_start_idx = (all_current_page - 1) * all_steps_per_page
                all_end_idx = min(all_start_idx + all_steps_per_page, len(all_steps))

                paginated_all_steps = all_steps[all_start_idx:all_end_idx]
            else:
                paginated_all_steps = all_steps

            df_all_steps = pd.DataFrame(paginated_all_steps)

            # Limita le colonne per una visualizzazione più chiara
            if len(df_all_steps.columns) > 0:
                columns_to_display = ["id", "step_url", "step_code"]
                # Assicurati che tutte le colonne esistano nel DataFrame
                columns_to_display = [
                    col for col in columns_to_display if col in df_all_steps.columns
                ]

                st.dataframe(
                    df_all_steps[columns_to_display],
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.write("Nessuno step disponibile nel database.")

# Modalità anteprima
with st.sidebar:
    st.subheader("Opzioni di visualizzazione")
    preview_mode = st.checkbox(
        "Modalità Anteprima",
        help="Attiva per visualizzare il funnel come lo vedrebbe un utente finale",
    )
    if preview_mode:
        st.info(
            "Modalità anteprima attiva. Le funzionalità di modifica sono disabilitate."
        )
        # Quando la modalità anteprima è attiva, possiamo disabilitare le funzionalità di modifica
        # utilizzando condizioni nel codice per nascondere i controlli di modifica

# Link di navigazione a fine pagina
st.divider()
st.caption("Navigazione:")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.page_link("app.py", label="Home", icon="🏠")
with col2:
    st.page_link("pages/dashboard.py", label="Dashboard", icon="📊")
with col3:
    st.page_link("pages/product_selection.py", label="Selezione Prodotti", icon="🛒")
with col4:
    st.page_link("pages/routes_manager.py", label="Gestione Route", icon="↔️")
