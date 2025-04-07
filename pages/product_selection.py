import pandas as pd
import streamlit as st

from db.funnel_operations import (
    create_product_funnel,
    get_funnel_by_product_id,
    get_products,
)

# Configurazione della pagina
st.title("Selezione Prodotto")

# Inizializzazione delle variabili di sessione
if "funnel_id" not in st.session_state:
    st.session_state.funnel_id = None
if "workflow_id" not in st.session_state:
    st.session_state.workflow_id = None
if "selected_product_id" not in st.session_state:
    st.session_state.selected_product_id = None
if "selected_product_name" not in st.session_state:
    st.session_state.selected_product_name = None


# Usiamo st.cache_data per le operazioni di database
@st.cache_data(ttl=300)
def cached_get_products():
    """Recupera l'elenco dei prodotti dal database con caching."""
    return get_products()


def update_product_selection():
    """Callback: Aggiorna lo stato del prodotto selezionato."""
    product_id = st.session_state.product_selector
    if product_id:
        # Trova il nome del prodotto selezionato
        for product in cached_get_products():
            if product["id"] == product_id:
                st.session_state.selected_product_name = (
                    product["title"] or product["code"]
                )
                break

        st.session_state.selected_product_id = product_id

        # Verifica se esiste già un funnel per questo prodotto
        funnel = get_funnel_by_product_id(product_id)
        if funnel:
            st.session_state.funnel_id = funnel["id"]
            st.session_state.workflow_id = funnel["workflow_id"]
            # Imposta la notifica
            st.session_state.notification = {
                "type": "info",
                "message": f"Funnel esistente caricato (ID: {funnel['id']})",
            }
        else:
            st.session_state.funnel_id = None
            st.session_state.workflow_id = None


def create_funnel():
    """Callback: Crea un nuovo funnel per il prodotto selezionato."""
    if st.session_state.selected_product_id and st.session_state.selected_product_name:
        with st.spinner("Creazione funnel in corso..."):
            result = create_product_funnel(
                st.session_state.selected_product_id,
                st.session_state.selected_product_name,
            )

            if not result["error"]:
                st.session_state.funnel_id = result["funnel"]["id"]
                st.session_state.workflow_id = result["funnel"]["workflow_id"]
                # Imposta la notifica
                st.session_state.notification = {
                    "type": "success",
                    "message": result["message"],
                }
                # Naviga alla pagina di gestione degli step
                st.switch_page("pages/steps_manager.py")
            else:
                # Imposta la notifica di errore
                st.session_state.notification = {
                    "type": "error",
                    "message": result["message"],
                }
                # Se esiste già un funnel, aggiorna lo stato con i dati del funnel esistente
                if "funnel" in result:
                    st.session_state.funnel_id = result["funnel"]["id"]
                    st.session_state.workflow_id = result["funnel"]["workflow_id"]


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

# Invalidazione condizionale della cache
if (
    "invalidate_product_cache" in st.session_state
    and st.session_state.invalidate_product_cache
):
    cached_get_products.clear()
    st.session_state.invalidate_product_cache = False

# Recupera l'elenco dei prodotti utilizzando la funzione cached
products = cached_get_products()

if products:
    # Container con bordo per la selezione del prodotto
    with st.container(border=True):
        # Aggiungi un campo di ricerca/filtro
        search_term = st.text_input(
            "🔍 Cerca prodotto (per codice o titolo):", key="product_search"
        )

        if search_term:
            # Filtra i prodotti in base al termine di ricerca
            filtered_products = [
                p
                for p in products
                if (p["code"] and search_term.lower() in p["code"].lower())
                or (p["title"] and search_term.lower() in p["title"].lower())
                or (
                    p["description"] and search_term.lower() in p["description"].lower()
                )
            ]
        else:
            filtered_products = products

        # Mostra il numero di prodotti trovati
        st.caption(f"{len(filtered_products)} prodotti trovati")

        # Crea un dizionario per il formato di visualizzazione nel selectbox
        product_options = {
            p["id"]: f"{p['title'] or 'N/A'} ({p['code']})" for p in filtered_products
        }

        # Aggiungi un'opzione vuota all'inizio
        product_options = {None: "Seleziona un prodotto..."} | product_options

        # Selectbox per la selezione del prodotto
        st.selectbox(
            "Seleziona un prodotto:",
            options=list(product_options.keys()),
            format_func=lambda x: product_options.get(x, "Sconosciuto"),
            key="product_selector",
            on_change=update_product_selection,
        )

    # Mostra i dettagli del prodotto selezionato
    if st.session_state.selected_product_id:
        with st.container(border=True):
            selected_product = next(
                (
                    p
                    for p in products
                    if p["id"] == st.session_state.selected_product_id
                ),
                None,
            )
            if selected_product:
                st.subheader("Prodotto selezionato:")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("ID", selected_product["id"])
                    st.metric("Codice", selected_product["code"])
                with col2:
                    st.metric("Titolo", selected_product["title"] or "N/A")

                with st.expander("Descrizione completa"):
                    st.write(
                        selected_product["description"]
                        or "Nessuna descrizione disponibile"
                    )

        # Verifica se esiste già un funnel per questo prodotto
        if st.session_state.funnel_id:
            st.info(
                f"Esiste già un funnel per questo prodotto (ID: {st.session_state.funnel_id})"
            )
            st.write(f"Workflow ID: {st.session_state.workflow_id}")

            # Pulsante per passare alla gestione degli step
            if st.button(
                "Gestisci Step del Funnel",
                type="primary",
                help="Passa alla scheda di gestione degli step",
            ):
                st.switch_page("pages/steps_manager.py")
        else:
            # Pulsante per creare un nuovo funnel
            st.button(
                "Crea Funnel per Prodotto selezionato",
                on_click=create_funnel,
                type="primary",
            )
else:
    st.error("Impossibile recuperare l'elenco dei prodotti dal database.")
    if st.button("Riprova", on_click=lambda: cached_get_products.clear()):
        st.rerun()

# Link di navigazione a fine pagina
st.divider()
st.caption("Navigazione:")
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("app.py", label="Home", icon="🏠")
with col3:
    if st.session_state.funnel_id:
        st.page_link("pages/steps_manager.py", label="Gestisci Step", icon="🔄")
