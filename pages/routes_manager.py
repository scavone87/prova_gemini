import streamlit as st
import json
import pandas as pd
from db.route_operations import get_routes_for_workflow, create_route, delete_route
from db.step_operations import get_steps

# Configurazione della pagina
st.title("Gestione Route del Funnel")

# Utilizzo di st.cache_data per le operazioni di database
@st.cache_data(ttl=300)
def cached_get_steps():
    """Recupera tutti gli step dal database con caching."""
    return get_steps()

@st.cache_data(ttl=300)
def cached_get_routes_for_workflow(workflow_id):
    """Recupera le route per un workflow specifico con caching."""
    if workflow_id:
        return get_routes_for_workflow(workflow_id)
    return []

def validate_json_input(json_string):
    """Valida un input JSON e restituisce un dizionario o None."""
    if not json_string:
        return None
    
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        return "error"

def handle_route_creation():
    """Gestisce la creazione di una nuova route tramite form."""
    # Validazione dei campi obbligatori
    if not st.session_state.next_step_id:
        st.session_state.notification = {
            'type': 'warning',
            'message': "È necessario specificare lo step di destinazione"
        }
        return
    
    # Validazione della configurazione JSON
    route_config = validate_json_input(st.session_state.route_config)
    if route_config == "error":
        st.session_state.notification = {
            'type': 'error',
            'message': "Il formato JSON della configurazione route non è valido"
        }
        return
    
    # Creazione della route
    result = create_route(
        st.session_state.workflow_id,
        st.session_state.from_step_id,  # Può essere None per lo step iniziale
        st.session_state.next_step_id,
        route_config
    )
    
    if not result['error']:
        # Imposta la notifica di successo
        st.session_state.notification = {
            'type': 'success',
            'message': result['message']
        }
        # Invalida la cache delle route
        st.session_state.invalidate_route_cache = True
        # Resetta i campi del form
        st.session_state.route_config = ""
        # Ricarica la pagina
        st.rerun()
    else:
        # Imposta la notifica di errore
        st.session_state.notification = {
            'type': 'error',
            'message': result['message']
        }

def delete_route_callback(route_id):
    """Callback per eliminare una route."""
    if route_id:
        result = delete_route(route_id)
        
        if not result['error']:
            # Imposta la notifica di successo
            st.session_state.notification = {
                'type': 'success',
                'message': result['message']
            }
            # Invalida la cache delle route
            st.session_state.invalidate_route_cache = True
            # Ricarica la pagina
            st.rerun()
        else:
            # Imposta la notifica di errore
            st.session_state.notification = {
                'type': 'error',
                'message': result['message']
            }

# Mostra le notifiche
if 'notification' in st.session_state and st.session_state.notification:
    notification_type = st.session_state.notification['type']
    message = st.session_state.notification['message']
    
    if notification_type == 'success':
        st.success(message)
    elif notification_type == 'info':
        st.info(message)
    elif notification_type == 'warning':
        st.warning(message)
    elif notification_type == 'error':
        st.error(message)
    
    # Reset della notifica dopo la visualizzazione
    st.session_state.notification = None

# Verifica se è stato selezionato un prodotto e un funnel
if 'selected_product_id' not in st.session_state or 'funnel_id' not in st.session_state or not st.session_state.selected_product_id or not st.session_state.funnel_id:
    st.warning("Seleziona prima un prodotto e crea un funnel nella pagina 'Selezione Prodotto'.")
    
    # Pulsante per tornare alla selezione del prodotto
    st.page_link("pages/product_selection.py", label="Vai a Selezione Prodotti", icon="🛒")
    st.stop()

st.subheader(f"Funnel per: {st.session_state.selected_product_name}")

# Uso di expander per mostrare informazioni tecniche quando necessario
with st.expander("Dettagli tecnici"):
    st.write(f"Funnel ID: {st.session_state.funnel_id}")
    st.write(f"Workflow ID: {st.session_state.workflow_id}")

# Invalidazione condizionale della cache
if 'invalidate_route_cache' in st.session_state and st.session_state.invalidate_route_cache:
    cached_get_routes_for_workflow.clear()
    st.session_state.invalidate_route_cache = False

# Layout a colonne per una migliore organizzazione
col1, col2 = st.columns([2, 3])

with col1:
    # Form per la creazione di una nuova route
    with st.container(border=True):
        st.subheader("Crea Nuovo Collegamento (Route)")
        
        # Recupera tutti gli step disponibili
        all_steps = cached_get_steps()
        
        if all_steps:
            # Crea un dizionario per il formato di visualizzazione nel selectbox
            step_options = {s['id']: f"{s['step_url']} ({s['step_code'] or 'No code'})" for s in all_steps}
            
            # Uso st.form per raggruppare i controlli e ridurre i reruns
            with st.form(key="create_route_form"):
                # Step di partenza (può essere None per lo step iniziale)
                st.selectbox(
                    "Da Step:",
                    options=[None] + list(step_options.keys()),
                    format_func=lambda x: "Step iniziale (ingresso)" if x is None else step_options.get(x, "Sconosciuto"),
                    key="from_step_id",
                    help="Lo step di partenza della route (None per lo step iniziale)"
                )
                
                # Step di destinazione (obbligatorio)
                st.selectbox(
                    "A Step:",
                    options=[None] + list(step_options.keys()),
                    format_func=lambda x: "Seleziona uno step..." if x is None else step_options.get(x, "Sconosciuto"),
                    key="next_step_id",
                    help="Lo step di destinazione della route (obbligatorio)"
                )
                
                # Configurazione della route
                st.text_area(
                    "Configurazione (JSON):",
                    key="route_config",
                    help="Configurazione della route in formato JSON (opzionale)",
                    height=150
                )
                
                # Pulsante submit
                submit_button = st.form_submit_button(
                    "Crea Collegamento",
                    type="primary",
                    help="Crea un nuovo collegamento tra gli step"
                )
                
                if submit_button:
                    handle_route_creation()
        else:
            st.warning("Nessuno step disponibile. Crea prima degli step nella pagina 'Gestione Step'.")
            
            # Pulsante per tornare alla gestione degli step
            st.page_link("pages/steps_manager.py", label="Vai a Gestione Step", icon="🔄")
    
    # Guida rapida per la creazione di route
    with st.expander("📌 Guida rapida"):
        st.markdown("""
        ### Come creare un collegamento (route):
        
        1. **Da Step**: Seleziona lo step di partenza (o "Step iniziale" per l'ingresso nel funnel)
        2. **A Step**: Seleziona lo step di destinazione (obbligatorio)
        3. **Configurazione**: Aggiungi una configurazione JSON opzionale per la route
        
        **Le route definiscono il percorso che l'utente può seguire nel funnel.**
        
        Per creare un funnel completo:
        - Inizia con una route dallo step iniziale al primo step
        - Collega tutti gli step in sequenza
        - Se necessario, crea percorsi alternativi (branch)
        """)

with col2:
    st.subheader("Route Esistenti")
    
    # Recupera le route associate al workflow corrente
    workflow_routes = cached_get_routes_for_workflow(st.session_state.workflow_id)
    
    if workflow_routes:
        # Raggruppa le route per step di partenza per una visualizzazione più organizzata
        routes_by_source = {}
        for route in workflow_routes:
            source_id = route['from_step']['id'] if route['from_step'] else None
            if source_id not in routes_by_source:
                routes_by_source[source_id] = []
            routes_by_source[source_id].append(route)
        
        # Visualizza il numero totale di route
        st.caption(f"Totale: {len(workflow_routes)} collegamenti")
        
        # Visualizza le route raggruppate per step di partenza
        for source_id, routes in routes_by_source.items():
            # Determina il titolo del gruppo
            group_title = "Dall'ingresso del funnel:" if source_id is None else f"Da step {source_id} ({routes[0]['from_step']['url']}):"
            
            # Crea un container per il gruppo
            with st.container(border=True):
                st.markdown(f"**{group_title}**")
                
                # Visualizza ogni route nel gruppo
                for route in routes:
                    cols = st.columns([3, 1, 3, 1])
                    
                    # Da step
                    with cols[0]:
                        from_label = "Ingresso" if route['from_step'] is None else f"{route['from_step']['url']}"
                        st.markdown(f"**Da:** {from_label}")
                        if route['from_step'] and route['from_step'].get('code'):
                            st.caption(f"Codice: {route['from_step']['code']}")
                    
                    # Freccia
                    with cols[1]:
                        st.markdown("➡️")
                    
                    # A step
                    with cols[2]:
                        st.markdown(f"**A:** {route['next_step']['url']}")
                        if route['next_step'].get('code'):
                            st.caption(f"Codice: {route['next_step']['code']}")
                    
                    # Azioni
                    with cols[3]:
                        # Uso di una chiave univoca per ogni bottone
                        unique_key = f"delete_route_{route['id']}"
                        st.button(
                            "❌", 
                            key=unique_key,
                            help="Elimina questa route",
                            on_click=delete_route_callback,
                            args=(route['id'],)
                        )
                    
                    # Config (se presente)
                    if route['route_config']:
                        with st.expander("Configurazione"):
                            st.json(route['route_config'])
                    
                    # Aggiungi un separatore tra le route
                    if route != routes[-1]:
                        st.divider()
        
        # Visualizzazione grafica del funnel
        with st.expander("🔄 Visualizzazione del funnel", expanded=True):
            st.caption("Questa è una rappresentazione semplificata del flusso del funnel.")
            
            # Implementa una visualizzazione semplice
            steps_in_funnel = set()
            for route in workflow_routes:
                if route['from_step']:
                    steps_in_funnel.add((route['from_step']['id'], route['from_step']['url']))
                steps_in_funnel.add((route['next_step']['id'], route['next_step']['url']))
            
            # Crea un grafico semplice usando ASCII art o Markdown
            st.write(f"Il funnel contiene {len(steps_in_funnel)} step connessi da {len(workflow_routes)} route.")
            
            # Mostra un elenco numerico di tutti gli step nel funnel
            st.markdown("**Step nel funnel:**")
            # Ordina gli step, gestendo i valori None
            sorted_steps = sorted(steps_in_funnel, key=lambda x: x[0] if x[0] is not None else -1)
            for i, (step_id, step_url) in enumerate(sorted_steps):
                st.markdown(f"{i+1}. Step {step_id}: `{step_url}`")
            
            # In futuro, potremmo integrare una visualizzazione grafica più sofisticata
            st.caption("Una visualizzazione grafica più avanzata sarà disponibile nelle prossime versioni.")
    else:
        st.info("Nessuna route definita per questo workflow. Crea nuove route per collegare gli step.")
        
        # Suggerimenti se non ci sono route
        if not workflow_routes:
            st.markdown("""
            ### Suggerimenti:
            1. Crea un collegamento dall'ingresso del funnel a uno step esistente
            2. Collega gli step in sequenza per definire il percorso del funnel
            """)

# Link di navigazione a fine pagina
st.divider()
st.caption("Navigazione:")
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("app.py", label="Home", icon="🏠")
with col2:
    st.page_link("pages/steps_manager.py", label="Gestione Step", icon="🔄")
with col3:
    st.page_link("pages/ui_configurator.py", label="Configurazione UI", icon="🎨")