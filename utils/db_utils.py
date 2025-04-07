import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from utils.error_handler import log_operation

# Configurazione del logging
logger = logging.getLogger(__name__)

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configurazione del database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "funnel_manager")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Stringa di connessione al database
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Creazione dell'engine SQLAlchemy con connection pooling ottimizzato
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Aumentato per supportare più connessioni simultanee
    max_overflow=20,  # Aumentato per gestire picchi di carico
    pool_timeout=30,
    pool_recycle=1800,  # Ricicla le connessioni dopo 30 minuti
    pool_pre_ping=True,  # Verifica che la connessione sia attiva prima dell'uso
    echo=False,  # Imposta su True solo in sviluppo per loggare le query SQL
)

# Creazione della sessione factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Crea e restituisce una nuova sessione del database.

    Returns:
        Session: Una sessione SQLAlchemy.
    """
    session = SessionLocal()
    try:
        return session
    except Exception as e:
        session.close()
        logger.error(f"Errore nella creazione della sessione DB: {e}")
        raise


def close_db_session(session):
    """Chiude una sessione del database.

    Args:
        session (Session): La sessione SQLAlchemy da chiudere.
    """
    if session:
        session.close()


def test_connection():
    """Testa la connessione al database.

    Returns:
        bool: True se la connessione è riuscita, False altrimenti.
    """
    try:
        session = get_db_session()
        session.execute(text("SELECT 1"))
        close_db_session(session)
        logger.info("Connessione al database riuscita.")
        return True
    except Exception as e:
        logger.error(f"Errore nella connessione al database: {e}")
        return False


def execute_paginated_query(
    query, page: int = 1, page_size: int = 10, log_action: str = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Esegue una query con paginazione e restituisce i risultati paginati e il conteggio totale.

    Args:
        query: Query SQLAlchemy da eseguire
        page: Numero di pagina (1-based)
        page_size: Numero di elementi per pagina
        log_action: Descrizione dell'azione per il logging (opzionale)

    Returns:
        Tuple[List[Dict], int]: Tupla contenente i risultati paginati e il conteggio totale
    """
    session = get_db_session()
    try:
        # Calcola l'offset in base alla pagina
        offset = (page - 1) * page_size

        # Esegui la query con limite e offset
        paginated_query = query.limit(page_size).offset(offset)

        # Esegui la query paginata
        results = session.execute(paginated_query).all()

        # Converti i risultati in un formato più facilmente utilizzabile
        data = []
        for row in results:
            if hasattr(row, "_asdict"):  # Per risultati di type Row
                data.append(row._asdict())
            elif hasattr(row, "__table__"):  # Per oggetti ORM
                data.append(
                    {c.name: getattr(row, c.name) for c in row.__table__.columns}
                )
            else:  # Fallback per altri tipi
                data.append(dict(row) if isinstance(row, dict) else row)

        # Esegui una query di conteggio per determinare il numero totale di risultati
        count_query = query.with_only_columns([text("COUNT(*)")]).order_by(None)
        total_count = session.execute(count_query).scalar()

        if log_action:
            log_operation(
                f"Query paginata: {log_action}",
                {
                    "page": page,
                    "page_size": page_size,
                    "total": total_count,
                    "returned": len(data),
                },
            )

        return data, total_count
    except SQLAlchemyError as e:
        logger.error(f"Errore nell'esecuzione della query paginata: {e}")
        raise
    finally:
        close_db_session(session)


def optimize_query_execution(
    session, query, operation_name: str = "query generica"
) -> Any:
    """
    Esegue una query con logging delle performance e gestione degli errori.

    Args:
        session: Sessione SQLAlchemy
        query: Query SQLAlchemy da eseguire
        operation_name: Nome dell'operazione per il logging

    Returns:
        Any: Risultato della query
    """
    import time

    start_time = time.time()
    try:
        # Esegue la query
        result = session.execute(query)

        # Calcola il tempo di esecuzione
        execution_time = time.time() - start_time

        # Logga il risultato
        log_operation(
            f"Esecuzione {operation_name}",
            {"execution_time_ms": round(execution_time * 1000, 2)},
            level=logging.DEBUG,
        )

        return result
    except SQLAlchemyError as e:
        # Calcola comunque il tempo di esecuzione
        execution_time = time.time() - start_time

        # Logga l'errore
        logger.error(
            f"Errore nell'esecuzione di {operation_name}. "
            f"Tempo: {round(execution_time * 1000, 2)}ms. Errore: {str(e)}"
        )
        raise
