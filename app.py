"""
Applicazione Funnel Manager Dashboard

Questa è l'applicazione principale per la gestione dei funnel di marketing.
Fornisce un'interfaccia intuitiva per configurare e analizzare funnel multicanale.
"""

import logging
import os
import sys
import traceback
from datetime import datetime

import pandas as pd
import streamlit as st
from sqlalchemy import text

# Configurazione Streamlit
st.set_page_config(
    page_title="Funnel Manager Dashboard",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modifica l'importazione per utilizzare le funzioni disponibili
from db.funnel_operations import get_funnel_by_product_id, get_products
from utils.cache_manager import invalidate_all_caches, register_cache_clear_handlers
from utils.config import CONFIG, get_config
from utils.db_utils import close_db_session, get_db_session, test_connection

# Import moduli interni
from utils.error_handler import handle_error, log_operation, setup_logging

# Configurazione del logging
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Inizializza il logging con rotazione dei file
setup_logging(
    log_level=get_config("log_level", "INFO"),
    log_file=os.path.join(LOGS_DIR, "funnel_manager.log"),
    log_rotation=True,
)

# Ottieni un logger per questo modulo
logger = logging.getLogger(__name__)

# Registra l'avvio dell'applicazione
log_operation(
    "Avvio applicazione",
    {
        "version": get_config("version", "1.0.0"),
        "environment": os.environ.get("APP_ENV", "development"),
        "timestamp": datetime.now().isoformat(),
    },
)

# Verifica connessione database all'avvio
try:
    if not test_connection():
        st.error(
            "🚨 Impossibile connettersi al database. Verifica le credenziali e la connessione."
        )
        st.stop()
except Exception as e:
    st.error(f"🚨 Errore durante il test della connessione al database: {str(e)}")
    st.stop()

# Gestisce gli handler di cache
register_cache_clear_handlers()


def main():
    """Funzione principale dell'applicazione."""
    st.title("🧭 Funnel Manager Dashboard")

    # Informazioni di stato
    st.sidebar.title("Funnel Manager")
    st.sidebar.caption(f"Versione: {get_config('version', '1.0.0')}")

    # Mostra stato connessione
    conn_state = st.sidebar.empty()
    try:
        if test_connection():
            conn_state.success("✅ Database connesso")
        else:
            conn_state.error("❌ Database non connesso")
    except Exception as e:
        conn_state.error(f"❌ Errore di connessione: {str(e)}")

    # Pulisci la cache se richiesto
    if st.sidebar.button("🔄 Pulisci Cache"):
        invalidate_all_caches()
        st.rerun()

    # Contenuto della pagina principale
    st.write(
        """
    Benvenuto nel Funnel Manager Dashboard! Questa applicazione ti permette di:
    
    - Visualizzare e gestire funnel per i tuoi prodotti
    - Configurare step e percorsi utente
    - Analizzare le performance con metriche e grafici
    - Esportare e importare configurazioni di funnel
    """
    )

    # Carica statistiche di base
    try:
        session = get_db_session()
        query = text(
            """
            SELECT 
                (SELECT COUNT(*) FROM funnel_manager.funnel) as funnel_count,
                (SELECT COUNT(*) FROM funnel_manager.step) as step_count,
                (SELECT COUNT(*) FROM funnel_manager.route) as route_count,
                (SELECT COUNT(*) FROM product.products) as product_count
        """
        )
        stats = session.execute(query).fetchone()

        # Mostra metriche base
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Funnel", stats.funnel_count)
        with col2:
            st.metric("Step", stats.step_count)
        with col3:
            st.metric("Route", stats.route_count)
        with col4:
            st.metric("Prodotti", stats.product_count)

        # Recupera gli ultimi funnel modificati
        recent_funnels_query = text(
            """
            SELECT f.id, f.name, p.title_prod
            FROM funnel_manager.funnel f
            JOIN product.products p ON f.product_id = p.id
            ORDER BY f.id DESC
            LIMIT 5
        """
        )
        recent_funnels = session.execute(recent_funnels_query).fetchall()

        if recent_funnels:
            st.subheader("Funnel recenti")

            funnel_data = [
                {"ID": f.id, "Nome": f.name, "Prodotto": f.title_prod}
                for f in recent_funnels
            ]

            st.dataframe(pd.DataFrame(funnel_data), use_container_width=True)

    except Exception as e:
        error_details = handle_error(e, "Errore nel recupero delle statistiche")
        st.error(f"🚨 {error_details['message']}")
        if get_config("debug_mode", False):
            st.error(f"Dettagli: {error_details.get('stack_trace', '')}")
    finally:
        close_db_session(session)

    # Separatore
    st.divider()

    # Layout dei collegamenti alle pagine
    st.subheader("Navigazione rapida")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.page_link(
            "pages/dashboard.py",
            label="Dashboard Analisi",
            icon="📊",
            help="Visualizza metriche e grafici per analizzare le performance dei funnel",
        )

        st.page_link(
            "pages/product_selection.py",
            label="Selezione Prodotti",
            icon="🛒",
            help="Seleziona un prodotto per configurare il relativo funnel",
        )

    with col2:
        st.page_link(
            "pages/steps_manager.py",
            label="Gestione Step",
            icon="🔄",
            help="Configura gli step del funnel e le loro proprietà",
        )

        st.page_link(
            "pages/routes_manager.py",
            label="Gestione Route",
            icon="↔️",
            help="Definisci i percorsi tra gli step del funnel",
        )

    with col3:
        st.page_link(
            "pages/export_import.py",
            label="Esporta/Importa",
            icon="📤",
            help="Esporta e importa configurazioni di funnel",
        )

        st.page_link(
            "pages/ui_configurator.py",
            label="Configurazione UI",
            icon="🎨",
            help="Personalizza l'aspetto dell'interfaccia utente",
        )

    # Footer
    st.caption(
        f"© 2025 YourCompany Inc. - Ambiente: {os.environ.get('APP_ENV', 'development').upper()}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("🚨 Si è verificato un errore imprevisto nell'applicazione.")

        # In modalità sviluppo mostra l'errore completo
        if get_config("debug_mode", False) or os.environ.get("APP_ENV") != "production":
            st.error(f"Errore: {str(e)}")
            st.code(traceback.format_exc())

        # Log dell'errore
        logger.exception("Errore non gestito nell'applicazione principale:")

        # Pulsante per ricaricare l'app
        if st.button("🔄 Ricarica applicazione"):
            st.rerun()
