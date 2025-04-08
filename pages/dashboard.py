"""
Dashboard per visualizzare metriche e grafici relativi ai funnel.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import func, select, text

from db.models import Funnel, Product, Route, Step, Workflow
from utils.db_utils import close_db_session, get_db_session, optimize_query_execution
from utils.error_handler import handle_error, log_operation

# Configurazione del logging
logger = logging.getLogger(__name__)

# Configurazione della pagina
st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("📊 Dashboard Funnel Manager")


# Ottenere statistiche generali del sistema
@st.cache_data(ttl=1800)  # Cache per 30 minuti
def get_system_stats():
    """Recupera le statistiche generali del sistema."""
    session = get_db_session()
    try:
        with st.spinner("Caricamento delle statistiche del sistema..."):
            # Conteggio prodotti totali
            products_count = (
                optimize_query_execution(
                    session, select(func.count(Product.id)), "conteggio prodotti"
                ).scalar()
                or 0
            )

            # Conteggio funnel totali
            funnels_count = (
                optimize_query_execution(
                    session, select(func.count(Funnel.id)), "conteggio funnel"
                ).scalar()
                or 0
            )

            # Conteggio step totali
            steps_count = (
                optimize_query_execution(
                    session, select(func.count(Step.id)), "conteggio step"
                ).scalar()
                or 0
            )

            # Conteggio route totali
            routes_count = (
                optimize_query_execution(
                    session, select(func.count(Route.id)), "conteggio route"
                ).scalar()
                or 0
            )

            # Media di step per funnel
            if funnels_count > 0:
                # Query personalizzata per contare gli step per ogni workflow
                steps_per_funnel_query = text(
                    """
                    SELECT AVG(step_count) as average_steps
                    FROM (
                        SELECT f.id as funnel_id, COUNT(DISTINCT r.nextstep_id) as step_count
                        FROM funnel_manager.funnel f
                        JOIN funnel_manager.workflow w ON f.workflow_id = w.id
                        LEFT JOIN funnel_manager.route r ON w.id = r.workflow_id
                        GROUP BY f.id
                    ) as step_counts
                """
                )

                avg_steps_per_funnel = (
                    optimize_query_execution(
                        session, steps_per_funnel_query, "media step per funnel"
                    ).scalar()
                    or 0
                )
            else:
                avg_steps_per_funnel = 0

            # Media di route per funnel
            if funnels_count > 0:
                # Query personalizzata per contare le route per ogni workflow
                routes_per_funnel_query = text(
                    """
                    SELECT AVG(route_count) as average_routes
                    FROM (
                        SELECT f.id as funnel_id, COUNT(r.id) as route_count
                        FROM funnel_manager.funnel f
                        JOIN funnel_manager.workflow w ON f.workflow_id = w.id
                        LEFT JOIN funnel_manager.route r ON w.id = r.workflow_id
                        GROUP BY f.id
                    ) as route_counts
                """
                )

                avg_routes_per_funnel = (
                    optimize_query_execution(
                        session, routes_per_funnel_query, "media route per funnel"
                    ).scalar()
                    or 0
                )
            else:
                avg_routes_per_funnel = 0

            # Recupero degli ultimi funnel creati
            latest_funnels_query = text(
                """
                SELECT f.id, f.name, p.title_prod as product_name, p.id as product_id
                FROM funnel_manager.funnel f
                JOIN product.products p ON f.product_id = p.id
                ORDER BY f.id DESC
                LIMIT 5
            """
            )

            latest_funnels = optimize_query_execution(
                session, latest_funnels_query, "ultimi funnel creati"
            ).fetchall()

            # Formatta i risultati
            latest_funnels_data = []
            for funnel in latest_funnels:
                latest_funnels_data.append(
                    {
                        "id": funnel.id,
                        "name": funnel.name,
                        "product_name": funnel.product_name or "Prodotto senza titolo",
                        "product_id": funnel.product_id,
                    }
                )

            return {
                "products_count": products_count,
                "funnels_count": funnels_count,
                "steps_count": steps_count,
                "routes_count": routes_count,
                "avg_steps_per_funnel": round(avg_steps_per_funnel, 1),
                "avg_routes_per_funnel": round(avg_routes_per_funnel, 1),
                "latest_funnels": latest_funnels_data,
            }
    except Exception as e:
        logger.error(f"Errore nel recupero delle statistiche del sistema: {e}")
        return handle_error(
            e,
            "Errore nel recupero delle statistiche del sistema",
            fallback_data={
                "products_count": 0,
                "funnels_count": 0,
                "steps_count": 0,
                "routes_count": 0,
                "avg_steps_per_funnel": 0,
                "avg_routes_per_funnel": 0,
                "latest_funnels": [],
            },
        ).get("data")
    finally:
        close_db_session(session)


@st.cache_data(ttl=1800)  # Cache per 30 minuti
def get_funnel_stats(funnel_id: Optional[int] = None):
    """
    Recupera le statistiche dettagliate per un funnel specifico o per tutti.
    """
    session = get_db_session()
    try:
        with st.spinner("Analisi dei dati del funnel in corso..."):
            # Se viene specificato un funnel_id, filtriamo i dati per quel funnel
            if funnel_id:
                # Query per recuperare informazioni sul funnel selezionato
                funnel_query = text(
                    """
                    SELECT f.id, f.name, p.title_prod as product_name, w.id as workflow_id
                    FROM funnel_manager.funnel f
                    JOIN product.products p ON f.product_id = p.id
                    JOIN funnel_manager.workflow w ON f.workflow_id = w.id
                    WHERE f.id = :funnel_id
                """
                )

                # Esegui la query con i parametri corretti
                funnel_data = optimize_query_execution(
                    session,
                    funnel_query.bindparams(funnel_id=int(funnel_id)),
                    f"dettagli funnel {funnel_id}"
                ).fetchone()

                if not funnel_data:
                    return {
                        "error": True,
                        "message": f"Funnel con ID {funnel_id} non trovato",
                    }

                workflow_id = funnel_data.workflow_id

                # Query per recuperare gli step del funnel
                steps_query = text(
                    """
                    SELECT DISTINCT s.id, s.step_url, s.step_code
                    FROM funnel_manager.step s
                    JOIN funnel_manager.route r ON s.id = r.nextstep_id OR s.id = r.fromstep_id
                    WHERE r.workflow_id = :workflow_id
                """
                )

                steps = (
                    optimize_query_execution(
                        session, steps_query, f"step del funnel {funnel_id}"
                    )
                    .bindparams(workflow_id=workflow_id)
                    .fetchall()
                )

                # Query per recuperare le route del funnel
                routes_query = text(
                    """
                    SELECT
                        r.id,
                        fs.step_url as from_step_url,
                        ns.step_url as to_step_url,
                        fs.id as from_step_id,
                        ns.id as to_step_id
                    FROM funnel_manager.route r
                    LEFT JOIN funnel_manager.step fs ON r.fromstep_id = fs.id
                    LEFT JOIN funnel_manager.step ns ON r.nextstep_id = ns.id
                    WHERE r.workflow_id = :workflow_id
                """
                )

                routes = (
                    optimize_query_execution(
                        session, routes_query, f"route del funnel {funnel_id}"
                    )
                    .bindparams(workflow_id=workflow_id)
                    .fetchall()
                )

                # Simuliamo alcuni dati di conversione per il grafico
                # (in un sistema reale questi dati verrebbero da un'analisi delle sessioni utente)
                conversion_data = []
                if steps:
                    total_users = 1000  # Esempio: utenti iniziali
                    steps_list = []
                    for i, step in enumerate(steps):
                        # Simuliamo un tasso di conversione decrescente tra il 70% e il 95%
                        conversion_rate = np.random.uniform(0.7, 0.95)
                        if i == 0:
                            users = total_users
                        else:
                            users = int(steps_list[i - 1]["users"] * conversion_rate)

                        steps_list.append(
                            {
                                "id": step.id,
                                "step_url": step.step_url,
                                "step_code": step.step_code or f"Step {step.id}",
                                "users": users,
                                "conversion_rate": conversion_rate if i > 0 else 1.0,
                            }
                        )

                    # Calcola il tasso di conversione complessivo
                    if len(steps_list) > 1:
                        overall_conversion = (
                            steps_list[-1]["users"] / steps_list[0]["users"]
                        )
                    else:
                        overall_conversion = 1.0

                    return {
                        "funnel": {
                            "id": funnel_data.id,
                            "name": funnel_data.name,
                            "product_name": funnel_data.product_name,
                        },
                        "steps": [dict(s) for s in steps],
                        "steps_count": len(steps),
                        "routes": [dict(r) for r in routes],
                        "routes_count": len(routes),
                        "conversion_data": steps_list,
                        "overall_conversion": overall_conversion,
                    }
                else:
                    return {
                        "funnel": {
                            "id": funnel_data.id,
                            "name": funnel_data.name,
                            "product_name": funnel_data.product_name,
                        },
                        "steps": [],
                        "steps_count": 0,
                        "routes": [],
                        "routes_count": 0,
                        "conversion_data": [],
                        "overall_conversion": 0,
                    }
            else:
                # Se non viene specificato un funnel_id, restituiamo statistiche aggregate
                # Top 5 funnel per numero di step
                top_funnels_query = text(
                    """
                    SELECT
                        f.id,
                        f.name,
                        p.title_prod as product_name,
                        COUNT(DISTINCT s.id) as step_count
                    FROM funnel_manager.funnel f
                    JOIN product.products p ON f.product_id = p.id
                    JOIN funnel_manager.workflow w ON f.workflow_id = w.id
                    JOIN funnel_manager.route r ON w.id = r.workflow_id
                    JOIN funnel_manager.step s ON r.fromstep_id = s.id OR r.nextstep_id = s.id
                    GROUP BY f.id, f.name, p.title_prod
                    ORDER BY step_count DESC
                    LIMIT 5
                """
                )

                top_funnels = optimize_query_execution(
                    session, top_funnels_query, "top 5 funnel per numero di step"
                ).fetchall()

                # Distribuzioni dei funnel per numero di step
                funnel_distribution_query = text(
                    """
                    SELECT
                        step_count,
                        COUNT(*) as funnel_count
                    FROM (
                        SELECT
                            f.id,
                            COUNT(DISTINCT s.id) as step_count
                        FROM funnel_manager.funnel f
                        JOIN funnel_manager.workflow w ON f.workflow_id = w.id
                        LEFT JOIN funnel_manager.route r ON w.id = r.workflow_id
                        LEFT JOIN funnel_manager.step s ON r.fromstep_id = s.id OR r.nextstep_id = s.id
                        GROUP BY f.id
                    ) as step_counts
                    GROUP BY step_count
                    ORDER BY step_count
                """
                )

                funnel_distribution = optimize_query_execution(
                    session,
                    funnel_distribution_query,
                    "distribuzione funnel per numero di step",
                ).fetchall()

                # Distribuzioni dei funnel per prodotto
                product_distribution_query = text(
                    """
                    SELECT
                        p.title_prod,
                        COUNT(f.id) as funnel_count
                    FROM funnel_manager.funnel f
                    JOIN product.products p ON f.product_id = p.id
                    GROUP BY p.title_prod
                    ORDER BY funnel_count DESC
                    LIMIT 10
                """
                )

                product_distribution = optimize_query_execution(
                    session,
                    product_distribution_query,
                    "distribuzione funnel per prodotto",
                ).fetchall()

                # Formatta i risultati
                return {
                    "top_funnels": [
                        {
                            "id": f.id,
                            "name": f.name,
                            "product_name": f.product_name,
                            "step_count": f.step_count,
                        }
                        for f in top_funnels
                    ],
                    "funnel_distribution": [
                        {"step_count": d.step_count, "funnel_count": d.funnel_count}
                        for d in funnel_distribution
                    ],
                    "product_distribution": [
                        {"title_prod": d.title_prod, "funnel_count": d.funnel_count}
                        for d in product_distribution
                    ],
                }
    except Exception as e:
        logger.error(f"Errore nel recupero delle statistiche del funnel: {e}")
        return handle_error(
            e,
            "Errore nel recupero delle statistiche del funnel",
            fallback_data={
                "top_funnels": [],
                "funnel_distribution": [],
                "product_distribution": [],
            },
        ).get("data")
    finally:
        close_db_session(session)


# Recupera le statistiche del sistema
system_stats = get_system_stats()

# Layout della dashboard
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Prodotti", system_stats["products_count"])

with col2:
    st.metric("Funnel", system_stats["funnels_count"])

with col3:
    st.metric("Step", system_stats["steps_count"])

with col4:
    st.metric("Route", system_stats["routes_count"])

st.divider()

# Visualizzazione di medie e statistiche aggiuntive
col1, col2 = st.columns(2)

with col1:
    st.metric("Media Step per Funnel", float(system_stats["avg_steps_per_funnel"]))

with col2:
    st.metric("Media Route per Funnel", float(system_stats["avg_routes_per_funnel"]))

st.divider()

# Sezione per i funnel specifici
st.subheader("Analisi Funnel Specifico")

# Lista di funnel disponibili
funnel_options = []
if system_stats.get("latest_funnels"):
    funnel_options = [{"id": None, "name": "Seleziona un funnel..."}]
    funnel_options.extend(
        [
            {"id": f["id"], "name": f"{f['name']} (ID: {f['id']})"}
            for f in system_stats["latest_funnels"]
        ]
    )

selected_funnel_idx = st.selectbox(
    "Seleziona un funnel per l'analisi dettagliata:",
    range(len(funnel_options)),
    format_func=lambda i: funnel_options[i]["name"],
)

selected_funnel_id = (
    funnel_options[selected_funnel_idx]["id"] if selected_funnel_idx > 0 else None
)

if selected_funnel_id:
    # Recupera i dati dettagliati del funnel selezionato
    funnel_details = get_funnel_stats(selected_funnel_id)

    if (
        funnel_details
        and not funnel_details.get("error")
        and "funnel" in funnel_details
    ):
        st.subheader(f"Dettagli del Funnel: {funnel_details['funnel']['name']}")
        st.caption(f"Prodotto: {funnel_details['funnel']['product_name']}")

        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

        with metrics_col1:
            st.metric("Numero di Step", funnel_details["steps_count"])

        with metrics_col2:
            st.metric("Numero di Route", funnel_details["routes_count"])

        with metrics_col3:
            st.metric(
                "Conversione Complessiva",
                f"{funnel_details.get('overall_conversion', 0):.1%}",
            )
    else:
        st.warning(
            f"Non sono disponibili dati dettagliati per il funnel selezionato. {funnel_details.get('message', 'Dati non disponibili')}"
        )
else:
    # Mostra statistiche aggregate su tutti i funnel
    funnel_stats = get_funnel_stats()

    if funnel_stats:
        # Visualizza i top funnel
        if funnel_stats.get("top_funnels"):
            st.subheader("Top 5 Funnel per Numero di Step")

            df_top_funnels = pd.DataFrame(funnel_stats["top_funnels"])

            # Grafico a barre con Altair per i top funnel
            top_funnel_chart = (
                alt.Chart(df_top_funnels)
                .mark_bar()
                .encode(
                    x=alt.X("name:N", title="Nome Funnel", sort="-y"),
                    y=alt.Y("step_count:Q", title="Numero di Step"),
                    color=alt.Color("step_count:Q", scale=alt.Scale(scheme="blues")),
                    tooltip=[
                        alt.Tooltip("name:N", title="Funnel"),
                        alt.Tooltip("step_count:Q", title="Numero di Step"),
                        alt.Tooltip("product_name:N", title="Prodotto"),
                        alt.Tooltip("id:Q", title="ID Funnel"),
                    ],
                )
                .properties(title="Funnel con più step", height=400)
            )

            st.altair_chart(top_funnel_chart, use_container_width=True)

        # Visualizza la distribuzione dei funnel per numero di step
        if funnel_stats.get("funnel_distribution"):
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Distribuzione Funnel per Numero di Step")

                df_distribution = pd.DataFrame(funnel_stats["funnel_distribution"])

                # Utilizziamo un grafico a torta nativo di Streamlit per la distribuzione
                distribution_chart = (
                    alt.Chart(df_distribution)
                    .mark_arc()
                    .encode(
                        theta=alt.Theta("funnel_count:Q", stack=True),
                        color=alt.Color(
                            "step_count:N", scale=alt.Scale(scheme="blues")
                        ),
                        tooltip=[
                            alt.Tooltip("step_count:N", title="Numero di Step"),
                            alt.Tooltip("funnel_count:Q", title="Numero di Funnel"),
                        ],
                    )
                    .properties(
                        title="Distribuzione dei Funnel per Numero di Step", height=400
                    )
                )

                st.altair_chart(distribution_chart, use_container_width=True)

            # Visualizza la distribuzione dei funnel per prodotto
            if funnel_stats.get("product_distribution"):
                with col2:
                    st.subheader("Distribuzione Funnel per Prodotto")

                    df_product_dist = pd.DataFrame(funnel_stats["product_distribution"])

                    # Grafico a barre orizzontale con Altair per i prodotti
                    product_chart = (
                        alt.Chart(df_product_dist)
                        .mark_bar()
                        .encode(
                            y=alt.Y("title_prod:N", title="Prodotto", sort="-x"),
                            x=alt.X("funnel_count:Q", title="Numero di Funnel"),
                            color=alt.Color(
                                "funnel_count:Q", scale=alt.Scale(scheme="viridis")
                            ),
                            tooltip=[
                                alt.Tooltip("title_prod:N", title="Prodotto"),
                                alt.Tooltip("funnel_count:Q", title="Numero di Funnel"),
                            ],
                        )
                        .properties(
                            title="Distribuzione dei Funnel per Prodotto", height=400
                        )
                    )

                    st.altair_chart(product_chart, use_container_width=True)
    else:
        st.info("Non sono disponibili dati statistici sui funnel.")

# Ultimi funnel creati
if system_stats.get("latest_funnels"):
    st.subheader("Ultimi Funnel Creati")

    df_latest = pd.DataFrame(
        [
            {"ID": f["id"], "Nome": f["name"], "Prodotto": f["product_name"]}
            for f in system_stats["latest_funnels"]
        ]
    )

    st.dataframe(df_latest, use_container_width=True)
else:
    st.info("Nessun funnel creato finora.")

# Link di navigazione a fine pagina
st.divider()
st.caption("Navigazione:")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.page_link("app.py", label="Home", icon="🏠")
with col2:
    st.page_link("pages/product_selection.py", label="Selezione Prodotti", icon="🛒")
with col3:
    st.page_link("pages/steps_manager.py", label="Gestione Step", icon="🔄")
with col4:
    st.page_link("pages/routes_manager.py", label="Gestione Route", icon="↔️")

# Aggiungi un footer con le informazioni sulla dashboard
st.sidebar.title("Informazioni")
st.sidebar.info(
    """
**Dashboard Funnel Manager**

Questa dashboard visualizza statistiche e metriche sui funnel di marketing.

I dati mostrati includono:
- Conteggi globali (prodotti, funnel, step, route)
- Analisi dei singoli funnel
- Grafici di conversione e abbandono
- Distribuzioni e statistiche aggregate

Per visualizzare dati dettagliati, seleziona un funnel specifico dal menu a tendina.
"""
)

# Aggiungi opzioni di refresh
st.sidebar.title("Opzioni")
if st.sidebar.button("🔄 Aggiorna Dati"):
    # Pulisci la cache per forzare il ricaricamento dei dati
    get_system_stats.clear()
    get_funnel_stats.clear()
    st.rerun()

# Aggiungi opzioni di intervallo temporale (per future implementazioni)
st.sidebar.title("Filtri Temporali")
st.sidebar.selectbox(
    "Intervallo di tempo",
    ["Ultimi 7 giorni", "Ultimo mese", "Ultimi 3 mesi", "Ultimo anno", "Tutti i tempi"],
    index=4,  # Default a "Tutti i tempi"
)

# Informazioni sul refresh dei dati
st.sidebar.caption(
    "I dati vengono aggiornati automaticamente ogni 30 minuti. Ultimo aggiornamento: "
    + pd.Timestamp.now().strftime("%H:%M:%S")
)
