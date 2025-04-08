"""
Pagina per l'esportazione e l'importazione delle configurazioni dei funnel.
"""

import json
import logging
from datetime import datetime

import pandas as pd
import streamlit as st

from db.funnel_operations import get_funnel_by_product_id
from utils.error_handler import handle_error, log_operation
from utils.export_import import (
    export_funnel_config,
    format_export_for_download,
    import_funnel_config,
)

# Configurazione del logging
logger = logging.getLogger(__name__)

# Configurazione della pagina
st.set_page_config(
    page_title="Esporta/Importa Funnel",
    page_icon="📤",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📤 Esporta / Importa Funnel")


# Funzione per generare un nome di file basato sul funnel
def generate_filename(funnel_name):
    """Genera un nome di file per l'export basato sul nome del funnel."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Rimuovi caratteri non validi per nomi file
    if funnel_name is None:
        safe_name = "unknown_funnel"
    else:
        safe_name = "".join(
            c if c.isalnum() or c in "._- " else "_" for c in funnel_name
        )
    return f"funnel_{safe_name}_{timestamp}.json"


# Funzione per caricare tutti i funnel disponibili
@st.cache_data(ttl=600)
def load_available_funnels():
    """Carica tutti i funnel disponibili dal database."""
    from sqlalchemy import text

    from utils.db_utils import close_db_session, get_db_session

    session = get_db_session()
    try:
        query = text(
            """
            SELECT
                f.id,
                f.name,
                f.workflow_id,
                p.id as product_id,
                p.title_prod as product_name
            FROM funnel_manager.funnel f
            JOIN product.products p ON f.product_id = p.id
            ORDER BY f.id DESC
        """
        )

        results = session.execute(query).fetchall()

        funnels = []
        for row in results:
            funnels.append(
                {
                    "id": row.id,
                    "name": row.name,
                    "product_id": row.product_id,
                    "product_name": row.product_name or "Prodotto senza nome",
                    "workflow_id": row.workflow_id,
                }
            )

        return funnels
    except Exception as e:
        return handle_error(
            e, "Errore nel recupero dei funnel disponibili", fallback_data=[]
        ).get("data", [])
    finally:
        close_db_session(session)


# Layout principale
tab1, tab2 = st.tabs(["Esportazione", "Importazione"])

with tab1:
    st.subheader("Esporta Configurazione Funnel")
    st.write(
        """
    Esporta la configurazione di un funnel in un file JSON.
    Il file conterrà tutti i dettagli sul funnel, inclusi step e route associati.
    """
    )

    # Carica i funnel disponibili
    funnels = load_available_funnels()

    if not funnels:
        st.warning("Non ci sono funnel disponibili per l'esportazione.")
    else:
        # Crea un selectbox per selezionare il funnel
        funnel_options = [
            f"{f['name']} - {f['product_name']} (ID: {f['id']})" for f in funnels
        ]
        selected_funnel_idx = st.selectbox(
            "Seleziona un funnel da esportare:",
            range(len(funnels)),
            format_func=lambda i: funnel_options[i],
        )

        selected_funnel = funnels[selected_funnel_idx]

        # Mostra dettagli del funnel selezionato
        with st.expander("Dettagli del funnel selezionato", expanded=True):
            st.write(f"**Nome del funnel:** {selected_funnel['name']}")
            st.write(f"**Prodotto:** {selected_funnel['product_name']}")
            st.write(f"**ID funnel:** {selected_funnel['id']}")
            st.write(f"**ID workflow:** {selected_funnel['workflow_id']}")

        # Opzioni di esportazione
        st.subheader("Opzioni di esportazione")
        export_sensitive = st.checkbox(
            "Includi dati sensibili",
            value=False,
            help="Se attivato, include dati sensibili come ID broker e configurazioni dettagliate",
        )

        # Pulsante di esportazione
        if st.button("📤 Esporta Funnel"):
            with st.spinner("Esportazione del funnel in corso..."):
                # Esporta la configurazione del funnel
                export_result = export_funnel_config(selected_funnel["id"])

                if not export_result.get("error", True):
                    # Formatta il JSON per il download
                    export_json = format_export_for_download(export_result)

                    # Genera un nome file significativo
                    funnel_name = selected_funnel.get("name")
                    filename = generate_filename(funnel_name)

                    # Aggiungi il pulsante di download
                    st.success(
                        f"Funnel esportato con successo! Clicca il pulsante qui sotto per scaricarlo."
                    )
                    st.download_button(
                        label="📥 Scarica configurazione funnel",
                        data=export_json,
                        file_name=filename,
                        mime="application/json",
                        key="download-funnel-json",
                    )

                    # Anteprima dei dati
                    with st.expander("Anteprima dei dati esportati"):
                        st.json(export_result["data"])
                else:
                    st.error(
                        f"Errore durante l'esportazione: {export_result.get('message', 'Errore sconosciuto')}"
                    )

with tab2:
    st.subheader("Importa Configurazione Funnel")
    st.write(
        """
    Importa una configurazione funnel da un file JSON.
    Il file deve essere nel formato generato dalla funzione di esportazione.
    """
    )

    # File uploader per il file JSON
    uploaded_file = st.file_uploader(
        "Carica un file di configurazione funnel (JSON)", type="json"
    )

    if uploaded_file is not None:
        try:
            # Leggi il contenuto del file
            import_data = json.load(uploaded_file)

            # Mostra anteprima dei dati importati
            with st.expander("Anteprima dei dati importati", expanded=True):
                # Estrai informazioni principali
                funnel_info = import_data.get("funnel", {})
                product_info = funnel_info.get("product", {})
                workflow_info = import_data.get("workflow", {})
                steps = import_data.get("steps", [])
                routes = import_data.get("routes", [])
                design_data = import_data.get("design", {})

                # Verifica se ci sono dati di design
                has_design = bool(design_data)
                sections = design_data.get("sections", [])
                components = design_data.get("components", [])
                structures = design_data.get("structures", [])
                cms_keys = design_data.get("cms_keys", [])

                st.write(f"**Funnel:** {funnel_info.get('name', 'N/A')}")
                st.write(
                    f"**Prodotto:** {product_info.get('name', 'N/A')} (Codice: {product_info.get('code', 'N/A')})"
                )
                st.write(f"**Workflow:** {workflow_info.get('description', 'N/A')}")
                st.write(f"**Numero di step:** {len(steps)}")
                st.write(f"**Numero di route:** {len(routes)}")

                if has_design:
                    st.write("---")
                    st.write("**Dati di design inclusi:**")
                    st.write(f"- Sezioni: {len(sections)}")
                    st.write(f"- Componenti: {len(components)}")
                    st.write(f"- Strutture: {len(structures)}")
                    st.write(f"- Chiavi CMS: {len(cms_keys)}")

                # Mostra tabella degli step
                if steps:
                    st.subheader("Step inclusi")
                    steps_df = pd.DataFrame(
                        [
                            {
                                "ID": s.get("id"),
                                "URL": s.get("step_url"),
                                "Codice": s.get("step_code", "N/A"),
                            }
                            for s in steps
                        ]
                    )
                    st.dataframe(steps_df, use_container_width=True)

            # Opzioni di importazione
            st.subheader("Opzioni di importazione")
            update_existing = st.checkbox(
                "Aggiorna funnel esistente",
                value=True,
                help="Se attivato e un funnel per lo stesso prodotto esiste già, lo aggiornerà invece di crearne uno nuovo",
            )

            st.info("L'aggiornamento di un funnel esistente è consigliato quando si importa un funnel che è stato precedentemente esportato e modificato. Questo garantisce che vengano aggiornati solo i dati modificati, mantenendo le relazioni esistenti.")

            # Mostra opzioni aggiuntive solo se ci sono dati di design
            if has_design:
                st.write("")
                st.write("**Opzioni per i dati di design:**")
                st.info("I dati di design includono sezioni, componenti, strutture e chiavi CMS che definiscono l'aspetto e il comportamento dell'interfaccia utente del funnel.")

            # Pulsante di importazione
            if st.button("📥 Importa Funnel"):
                with st.spinner("Importazione del funnel in corso..."):
                    # Importa la configurazione del funnel
                    import_result = import_funnel_config(import_data, update_existing)

                    if not import_result.get("error", True):
                        st.success(
                            f"{import_result.get('message', 'Importazione completata con successo')}"
                        )
                        st.write(f"Funnel ID: {import_result.get('funnel_id')}")
                        st.write(
                            f"Step importati: {import_result.get('steps_imported')}"
                        )
                        st.write(
                            f"Route importate: {import_result.get('routes_imported')}"
                        )

                        # Mostra informazioni sui dati di design importati se presenti
                        design_imported = import_result.get("design_imported")
                        if design_imported:
                            st.write("---")
                            st.write("**Dati di design importati:**")
                            st.write(f"- Sezioni: {design_imported.get('sections', 0)}")
                            st.write(f"- Componenti: {design_imported.get('components', 0)}")
                            st.write(f"- Strutture: {design_imported.get('structures', 0)}")
                            st.write(f"- Chiavi CMS: {design_imported.get('cms_keys', 0)}")

                        # Aggiungi link per navigare al funnel importato
                        st.page_link(
                            "pages/steps_manager.py",
                            label="Vai alla gestione degli step",
                            icon="🔄",
                        )
                    else:
                        st.error(
                            f"Errore durante l'importazione: {import_result.get('message', 'Errore sconosciuto')}"
                        )

        except json.JSONDecodeError:
            st.error(
                "Il file caricato non è un JSON valido. Verifica il formato del file."
            )
        except Exception as e:
            st.error(f"Errore durante l'elaborazione del file: {str(e)}")

# Aggiungi link alla pagina attuale dalla home
with st.sidebar:
    st.title("Esporta/Importa")
    st.info(
        """
    Questa pagina consente di:

    - **Esportare** le configurazioni dei funnel in formato JSON
    - **Importare** funnel da file JSON precedentemente esportati

    Utilizza l'esportazione per fare backup dei tuoi funnel o per trasferirli tra ambienti diversi.
    """
    )

# Link di navigazione a fine pagina
st.divider()
st.caption("Navigazione:")
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    st.page_link("app.py", label="Home", icon="🏠")
with col2:
    st.page_link("pages/dashboard.py", label="Dashboard", icon="📊")
with col3:
    st.page_link("pages/product_selection.py", label="Selezione Prodotti", icon="🛒")
with col4:
    st.page_link("pages/steps_manager.py", label="Gestione Step", icon="🔄")
