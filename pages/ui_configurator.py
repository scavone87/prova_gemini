import json

import pandas as pd
import streamlit as st

from db import step_operations, ui_operations
from utils.db_utils import get_db_session

# Configurazione della pagina
st.title("Configurazione UI per Step")

# Inizializzazione delle variabili di sessione
if "selected_product_id" not in st.session_state:
    st.session_state.selected_product_id = None

if "funnel_id" not in st.session_state:
    st.session_state.funnel_id = None

if "selected_product_name" not in st.session_state:
    st.session_state.selected_product_name = None

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

# Inizializzazione delle altre variabili di sessione
if "sections" not in st.session_state:
    st.session_state.sections = []

if "components" not in st.session_state:
    st.session_state.components = []

if "current_step_id" not in st.session_state:
    st.session_state.current_step_id = None


def load_steps():
    """Carica gli step dal funnel selezionato"""
    if st.session_state.funnel_id:
        steps = step_operations.get_steps_by_funnel(st.session_state.funnel_id)
        return steps
    return []


def load_sections():
    """Carica tutte le sezioni disponibili"""
    sections = ui_operations.get_sections()
    st.session_state.sections = sections
    return sections


def load_components():
    """Carica tutti i componenti disponibili"""
    components = ui_operations.get_components()
    st.session_state.components = components
    return components


def load_sections_for_step(step_id):
    """Carica le sezioni associate a uno step specifico"""
    product_id = (
        st.session_state.selected_product_id
        if "selected_product_id" in st.session_state
        else None
    )
    sections = ui_operations.get_sections_for_step(step_id, product_id=product_id)
    return sections


def load_components_for_section(section_id):
    """Carica i componenti associati a una sezione specifica"""
    components = ui_operations.get_components_for_section(section_id)
    return components


def add_new_section():
    """Aggiunge una nuova sezione al database"""
    if st.session_state.new_section_type:
        result = ui_operations.create_section(st.session_state.new_section_type)
        if not result["error"]:
            st.session_state.notification = {
                "type": "success",
                "message": result["message"],
            }
            load_sections()
        else:
            st.session_state.notification = {
                "type": "error",
                "message": result["message"],
            }
        st.session_state.new_section_type = ""
        st.rerun()


def add_new_component():
    """Aggiunge un nuovo componente al database"""
    if st.session_state.new_component_type:
        result = ui_operations.create_component(st.session_state.new_component_type)
        if not result["error"]:
            st.session_state.notification = {
                "type": "success",
                "message": result["message"],
            }
            load_components()
        else:
            st.session_state.notification = {
                "type": "error",
                "message": result["message"],
            }
        st.session_state.new_component_type = ""
        st.rerun()


def add_section_to_step():
    """Aggiunge una sezione allo step selezionato"""
    if (
        st.session_state.current_step_id
        and "selected_section" in st.session_state
        and st.session_state.selected_section
    ):

        # Trova l'ultimo ordine esistente e aggiungi 1
        existing_sections = load_sections_for_step(st.session_state.current_step_id)
        next_order = 1
        if existing_sections:
            orders = [section["order"] for section in existing_sections]
            next_order = max(orders) + 1 if orders else 1

        product_id = (
            st.session_state.selected_product_id
            if "selected_product_id" in st.session_state
            else None
        )

        result = ui_operations.add_section_to_step(
            st.session_state.current_step_id,
            st.session_state.selected_section,
            next_order,
            product_id=product_id,
        )

        if not result["error"]:
            st.session_state.notification = {
                "type": "success",
                "message": result["message"],
            }
        else:
            st.session_state.notification = {
                "type": "error",
                "message": result["message"],
            }
        st.rerun()


def add_component_to_section():
    """Aggiunge un componente alla sezione selezionata"""
    if (
        "selected_section_id" in st.session_state
        and "selected_component" in st.session_state
        and st.session_state.selected_section_id
        and st.session_state.selected_component
    ):

        # Trova l'ultimo ordine esistente e aggiungi 1
        existing_components = load_components_for_section(
            st.session_state.selected_section_id
        )
        next_order = 1
        if existing_components:
            orders = [component["order"] for component in existing_components]
            next_order = max(orders) + 1 if orders else 1

        result = ui_operations.add_component_to_section(
            st.session_state.selected_section_id,
            st.session_state.selected_component,
            next_order,
        )

        if not result["error"]:
            st.session_state.notification = {
                "type": "success",
                "message": result["message"],
            }
        else:
            st.session_state.notification = {
                "type": "error",
                "message": result["message"],
            }
        st.rerun()


def update_section_order(section_id, new_order):
    """Aggiorna l'ordine di una sezione"""
    result = ui_operations.update_step_section_order(section_id, new_order)
    if not result["error"]:
        st.session_state.notification = {
            "type": "success",
            "message": result["message"],
        }
    else:
        st.session_state.notification = {"type": "error", "message": result["message"]}
    st.rerun()


def update_component_order(component_section_id, new_order):
    """Aggiorna l'ordine di un componente"""
    result = ui_operations.update_component_section_order(
        component_section_id, new_order
    )
    if not result["error"]:
        st.session_state.notification = {
            "type": "success",
            "message": result["message"],
        }
    else:
        st.session_state.notification = {"type": "error", "message": result["message"]}
    st.rerun()


def delete_section_from_step(step_section_id):
    """Elimina una sezione da uno step"""
    result = ui_operations.delete_step_section(step_section_id)
    if not result["error"]:
        st.session_state.notification = {
            "type": "success",
            "message": result["message"],
        }
    else:
        st.session_state.notification = {"type": "error", "message": result["message"]}
    st.rerun()


def delete_component_from_section(component_section_id):
    """Elimina un componente da una sezione"""
    result = ui_operations.delete_component_section(component_section_id)
    if not result["error"]:
        st.session_state.notification = {
            "type": "success",
            "message": result["message"],
        }
    else:
        st.session_state.notification = {"type": "error", "message": result["message"]}
    st.rerun()


def update_structure_data(structure_id, new_data):
    """Aggiorna i dati di una struttura"""
    result = ui_operations.update_structure_data(structure_id, new_data)
    if not result["error"]:
        st.session_state.notification = {
            "type": "success",
            "message": result["message"],
        }
    else:
        st.session_state.notification = {"type": "error", "message": result["message"]}
    st.rerun()


def save_cms_key(structure_component_section_id, cms_data):
    """Salva o aggiorna una chiave CMS"""
    result = ui_operations.create_or_update_cms_key(
        structure_component_section_id, cms_data
    )
    if not result["error"]:
        st.session_state.notification = {
            "type": "success",
            "message": result["message"],
        }
    else:
        st.session_state.notification = {"type": "error", "message": result["message"]}
    st.rerun()


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

st.subheader(f"Personalizzazione UI per: {st.session_state.selected_product_name}")

# Caricamento dei dati
steps = load_steps()
all_sections = load_sections()
all_components = load_components()

# Layout a due colonne per la selezione dello step e la configurazione
col1, col2 = st.columns([1, 2])

with col1:
    with st.container(border=True):
        st.subheader("Selezione Step")

        # Selezione degli step dal funnel
        step_options = [(f"{step['order']}. {step['name']}") for step in steps]
        step_values = [step["id"] for step in steps]

        if step_options:
            step_index = 0
            if st.session_state.current_step_id:
                try:
                    step_index = step_values.index(st.session_state.current_step_id)
                except ValueError:
                    step_index = 0

            selected_step_name = st.selectbox(
                "Seleziona uno step da personalizzare:",
                options=step_options,
                index=step_index,
                key="ui_step_selector",
                help="Seleziona lo step per cui vuoi configurare l'interfaccia utente",
            )

            # Aggiorna l'ID dello step corrente
            selected_step_index = step_options.index(selected_step_name)
            st.session_state.current_step_id = step_values[selected_step_index]
        else:
            st.warning("Nessuno step trovato nel funnel selezionato.")

with col2:
    # Tabs per organizzare le diverse sezioni di configurazione
    tab1, tab2, tab3, tab4 = st.tabs(["Layout", "Sezioni", "Componenti", "Stile"])

    with tab1:
        st.subheader("Configurazione Layout")

        # Verifica se è stato selezionato uno step
        if st.session_state.current_step_id:
            # Opzioni di layout in un form
            with st.form("layout_form"):
                st.selectbox(
                    "Tipo di layout:",
                    options=[
                        "Singola colonna",
                        "Due colonne",
                        "Tre colonne",
                        "Sidebar",
                    ],
                    key="ui_layout_type",
                )

                st.slider(
                    "Larghezza contenuto (%)", 30, 100, 70, key="ui_content_width"
                )

                st.checkbox("Mostra header", value=True, key="ui_show_header")

                st.checkbox("Mostra footer", value=True, key="ui_show_footer")

                st.form_submit_button("Applica Layout")
        else:
            st.info("Seleziona uno step per configurare il layout.")

    with tab2:
        st.subheader("Gestione Sezioni")

        if st.session_state.current_step_id:
            # Sezione per aggiungere nuove sezioni al database
            with st.expander("Aggiungi nuova sezione"):
                st.text_input(
                    "Tipo di sezione",
                    key="new_section_type",
                    placeholder="Es. header, footer, form, results",
                )
                st.button("Aggiungi sezione al database", on_click=add_new_section)

            # Selezione delle sezioni esistenti da aggiungere allo step
            section_options = [section["sectiontype"] for section in all_sections]
            section_ids = [section["id"] for section in all_sections]

            st.selectbox(
                "Seleziona una sezione da aggiungere:",
                options=section_options,
                key="selected_section_display",
            )

            # Mappa il nome della sezione selezionata all'ID
            if (
                "selected_section_display" in st.session_state
                and st.session_state.selected_section_display
            ):
                try:
                    index = section_options.index(
                        st.session_state.selected_section_display
                    )
                    st.session_state.selected_section = section_ids[index]
                except ValueError:
                    st.session_state.selected_section = None

            # Pulsante per aggiungere la sezione selezionata allo step
            st.button("Aggiungi sezione allo step", on_click=add_section_to_step)

            # Mostra le sezioni già associate allo step
            st.subheader("Sezioni configurate per questo step")
            step_sections = load_sections_for_step(st.session_state.current_step_id)

            if step_sections:
                for section in step_sections:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            st.write(f"**{section['sectiontype']}**")
                            st.caption(f"Ordine: {section['order']}")

                            # Set section_id in session state when the section is selected
                            if st.button(
                                f"Seleziona",
                                key=f"select_section_{section['step_section_id']}",
                            ):
                                st.session_state.selected_section_id = section["id"]
                                st.rerun()

                        with col2:
                            # Pulsanti per riordinare la sezione
                            st.button(
                                "↑",
                                key=f"up_{section['step_section_id']}",
                                help="Sposta su",
                                on_click=update_section_order,
                                args=(
                                    section["step_section_id"],
                                    max(1, section["order"] - 1),
                                ),
                            )

                            st.button(
                                "↓",
                                key=f"down_{section['step_section_id']}",
                                help="Sposta giù",
                                on_click=update_section_order,
                                args=(section["step_section_id"], section["order"] + 1),
                            )

                        with col3:
                            # Pulsante per eliminare la sezione dallo step
                            st.button(
                                "🗑️",
                                key=f"delete_{section['step_section_id']}",
                                help="Elimina sezione",
                                on_click=delete_section_from_step,
                                args=(section["step_section_id"],),
                            )
            else:
                st.info(
                    "Nessuna sezione configurata per questo step. Aggiungi una sezione."
                )
        else:
            st.info("Seleziona uno step per gestire le sezioni.")

    with tab3:
        st.subheader("Gestione Componenti")

        # Verifica se è stata selezionata una sezione
        if (
            "selected_section_id" in st.session_state
            and st.session_state.selected_section_id
        ):
            # Recupera il tipo di sezione
            section_type = next(
                (
                    s["sectiontype"]
                    for s in all_sections
                    if s["id"] == st.session_state.selected_section_id
                ),
                "Sezione",
            )
            st.caption(f"Configurazione componenti per: {section_type}")

            # Sezione per aggiungere nuovi componenti al database
            with st.expander("Aggiungi nuovo componente"):
                st.text_input(
                    "Tipo di componente",
                    key="new_component_type",
                    placeholder="Es. title, text, image, button, form, table, chart",
                )
                st.button("Aggiungi componente al database", on_click=add_new_component)

            # Selezione dei componenti esistenti da aggiungere alla sezione
            component_options = [
                component["component_type"] for component in all_components
            ]
            component_ids = [component["id"] for component in all_components]

            st.selectbox(
                "Seleziona un componente da aggiungere:",
                options=component_options,
                key="selected_component_display",
            )

            # Mappa il nome del componente selezionato all'ID
            if (
                "selected_component_display" in st.session_state
                and st.session_state.selected_component_display
            ):
                try:
                    index = component_options.index(
                        st.session_state.selected_component_display
                    )
                    st.session_state.selected_component = component_ids[index]
                except ValueError:
                    st.session_state.selected_component = None

            # Pulsante per aggiungere il componente selezionato alla sezione
            st.button(
                "Aggiungi componente alla sezione", on_click=add_component_to_section
            )

            # Mostra i componenti già associati alla sezione
            st.subheader("Componenti configurati per questa sezione")
            section_components = load_components_for_section(
                st.session_state.selected_section_id
            )

            if section_components:
                for component in section_components:
                    with st.container(border=True):
                        st.write(f"**{component['component_type']}**")
                        st.caption(f"Ordine: {component['order']}")

                        # Visualizza la struttura JSON del componente se disponibile
                        if component["structure"]:
                            with st.expander("Struttura JSON"):
                                # Crea una chiave univoca per l'editor JSON
                                json_key = f"json_{component['component_section_id']}"

                                # Inizializza la chiave di sessione se non esiste
                                if json_key not in st.session_state:
                                    st.session_state[json_key] = json.dumps(
                                        component["structure"], indent=2
                                    )

                                # Editor JSON
                                json_str = st.text_area(
                                    "Modifica struttura JSON:",
                                    value=st.session_state[json_key],
                                    height=150,
                                    key=f"json_edit_{component['component_section_id']}",
                                )

                                # Aggiorna il valore nella sessione
                                st.session_state[json_key] = json_str

                                # Pulsante per salvare le modifiche alla struttura
                                if st.button(
                                    "Salva struttura",
                                    key=f"save_json_{component['component_section_id']}",
                                ):
                                    try:
                                        json_data = json.loads(json_str)
                                        update_structure_data(
                                            component["structure_id"], json_data
                                        )
                                    except json.JSONDecodeError:
                                        st.error(
                                            "JSON non valido. Controlla la sintassi."
                                        )

                        # Configurazione delle chiavi CMS
                        with st.expander("Configurazione CMS"):
                            # Ottieni la configurazione CMS esistente
                            cms_key = None
                            if component["structure_component_section_id"]:
                                cms_key = ui_operations.get_cms_key_for_structure(
                                    component["structure_component_section_id"]
                                )

                            cms_json_key = f"cms_{component['component_section_id']}"

                            # Inizializza la chiave di sessione con il valore esistente o vuoto
                            if cms_json_key not in st.session_state:
                                if cms_key and "value" in cms_key:
                                    st.session_state[cms_json_key] = json.dumps(
                                        cms_key["value"], indent=2
                                    )
                                else:
                                    st.session_state[cms_json_key] = "{}"

                            # Editor JSON per la chiave CMS
                            cms_json_str = st.text_area(
                                "Chiavi CMS (JSON):",
                                value=st.session_state[cms_json_key],
                                height=150,
                                key=f"cms_edit_{component['component_section_id']}",
                            )

                            # Aggiorna il valore nella sessione
                            st.session_state[cms_json_key] = cms_json_str

                            # Pulsante per salvare le modifiche alla chiave CMS
                            if st.button(
                                "Salva configurazione CMS",
                                key=f"save_cms_{component['component_section_id']}",
                            ):
                                try:
                                    cms_data = json.loads(cms_json_str)
                                    save_cms_key(
                                        component["structure_component_section_id"],
                                        cms_data,
                                    )
                                except json.JSONDecodeError:
                                    st.error("JSON non valido. Controlla la sintassi.")

                        # Azioni per il componente
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            # Pulsanti per riordinare il componente
                            st.button(
                                "↑",
                                key=f"up_comp_{component['component_section_id']}",
                                help="Sposta su",
                                on_click=update_component_order,
                                args=(
                                    component["component_section_id"],
                                    max(1, component["order"] - 1),
                                ),
                            )

                        with col2:
                            st.button(
                                "↓",
                                key=f"down_comp_{component['component_section_id']}",
                                help="Sposta giù",
                                on_click=update_component_order,
                                args=(
                                    component["component_section_id"],
                                    component["order"] + 1,
                                ),
                            )

                        with col3:
                            # Pulsante per eliminare il componente dalla sezione
                            st.button(
                                "🗑️",
                                key=f"delete_comp_{component['component_section_id']}",
                                help="Elimina componente",
                                on_click=delete_component_from_section,
                                args=(component["component_section_id"],),
                            )
            else:
                st.info(
                    "Nessun componente configurato per questa sezione. Aggiungi un componente."
                )
        else:
            st.info(
                "Seleziona prima una sezione dalla tab 'Sezioni' per gestire i componenti."
            )

    with tab4:
        st.subheader("Stile e Tema")

        if st.session_state.current_step_id:
            # Configurazione dei colori
            st.color_picker("Colore primario:", "#FF4B4B", key="ui_primary_color")
            st.color_picker("Colore secondario:", "#0068C9", key="ui_secondary_color")
            st.color_picker("Colore background:", "#FFFFFF", key="ui_bg_color")

            # Configurazione dei font
            st.selectbox(
                "Font primario:",
                options=[
                    "System default",
                    "Arial",
                    "Roboto",
                    "Montserrat",
                    "Open Sans",
                ],
                key="ui_primary_font",
            )

            # Configurazione delle spaziature
            st.slider("Padding (px)", 0, 50, 20, key="ui_padding")

            # Pulsante per applicare lo stile
            st.button("Applica stile", type="primary", key="apply_style")
        else:
            st.info("Seleziona uno step per configurare lo stile.")

# Anteprima dell'interfaccia
st.subheader("Anteprima")
with st.expander("Mostra anteprima", expanded=True):
    # Verifica se è stato selezionato uno step
    if st.session_state.current_step_id:
        # Carica le sezioni per lo step
        step_sections = load_sections_for_step(st.session_state.current_step_id)

        if step_sections:
            st.caption("Anteprima dell'interfaccia utente per lo step selezionato")

            # Crea un container per ogni sezione nell'ordine corretto
            for section in sorted(step_sections, key=lambda x: x["order"]):
                with st.container(border=True):
                    st.write(f"### Sezione: {section['sectiontype']}")

                    # Carica i componenti per questa sezione
                    section_components = load_components_for_section(section["id"])

                    if section_components:
                        for component in sorted(
                            section_components, key=lambda x: x["order"]
                        ):
                            st.write(f"**Componente: {component['component_type']}**")

                            # Mostra i dati della struttura se disponibili
                            if component["structure"]:
                                st.json(component["structure"])

                            # Mostra la chiave CMS se disponibile
                            if component["structure_component_section_id"]:
                                cms_key = ui_operations.get_cms_key_for_structure(
                                    component["structure_component_section_id"]
                                )
                                if cms_key and "value" in cms_key:
                                    st.caption("Dati CMS:")
                                    st.json(cms_key["value"])
                    else:
                        st.caption(
                            "Nessun componente in questa sezione. Aggiungi componenti dalla tab 'Componenti'."
                        )
        else:
            st.info(
                "Nessuna sezione configurata per questo step. Aggiungi sezioni dalla tab 'Sezioni'."
            )
    else:
        st.info("Seleziona uno step per visualizzare l'anteprima.")

    st.caption(
        "Nota: questa è una visualizzazione semplificata dell'interfaccia. Nel frontend reale, i componenti saranno renderizzati correttamente in base alla loro configurazione."
    )

# Link di navigazione a fine pagina
st.divider()
st.caption("Navigazione:")
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("app.py", label="Home", icon="🏠")
with col2:
    st.page_link("pages/product_selection.py", label="Selezione Prodotti", icon="🛒")
with col3:
    st.page_link("pages/routes_manager.py", label="Gestione Route", icon="↔️")
