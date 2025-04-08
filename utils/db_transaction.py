"""
Modulo per la gestione standardizzata delle transazioni del database.

Fornisce decoratori e utility per garantire transazioni atomiche e gestione
coerente degli errori nelle operazioni di database.
"""

import functools
import json
import logging
import time
from datetime import datetime

from sqlalchemy.exc import OperationalError, SQLAlchemyError, TimeoutError

from utils.db_utils import close_db_session, get_db_session

# Configurazione del logging
logger = logging.getLogger(__name__)


def standardized_db_operation(operation_name):
    """
    Decorator per standardizzare le operazioni di database.
    
    Gestisce automaticamente l'apertura e chiusura della sessione,
    le transazioni, il commit e il rollback, e il logging.
    
    Args:
        operation_name (str): Nome dell'operazione per il logging
        
    Returns:
        function: Funzione decorata
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            session = get_db_session()
            try:
                # Inizia una transazione esplicita
                session.begin()
                
                # Esegui la funzione con la sessione come primo argomento
                result = func(session, *args, **kwargs)
                
                # Commit della transazione
                session.commit()
                
                # Log dell'operazione riuscita
                logger.info(f"Operazione {operation_name} completata con successo")
                
                return result
            except SQLAlchemyError as e:
                # Rollback della transazione
                session.rollback()
                
                # Log dettagliato dell'errore
                logger.error(f"Errore SQL in {operation_name}: {str(e)}")
                
                # Restituisci una risposta di errore standardizzata
                return {
                    "error": True,
                    "message": f"Errore nell'operazione {operation_name}: {str(e)}",
                    "error_type": "database",
                    "details": str(e)
                }
            except Exception as e:
                # Rollback della transazione
                session.rollback()
                
                # Log dettagliato dell'errore
                logger.error(f"Errore generico in {operation_name}: {str(e)}")
                
                # Restituisci una risposta di errore standardizzata
                return {
                    "error": True,
                    "message": f"Errore nell'operazione {operation_name}: {str(e)}",
                    "error_type": "general",
                    "details": str(e)
                }
            finally:
                # Chiudi sempre la sessione
                close_db_session(session)
        
        return wrapper
    return decorator


def with_retry(max_attempts=3, retry_delay=0.5):
    """
    Decorator per riprovare operazioni di database in caso di errori di connessione.
    
    Args:
        max_attempts (int): Numero massimo di tentativi
        retry_delay (float): Ritardo tra i tentativi in secondi
        
    Returns:
        function: Funzione decorata
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, TimeoutError) as e:
                    last_exception = e
                    logger.warning(
                        f"Tentativo {attempt}/{max_attempts} fallito: {str(e)}. "
                        f"Riprovo tra {retry_delay} secondi..."
                    )
                    time.sleep(retry_delay)
            
            # Se arriviamo qui, tutti i tentativi sono falliti
            logger.error(f"Tutti i {max_attempts} tentativi falliti: {str(last_exception)}")
            raise last_exception
        
        return wrapper
    return decorator


def log_db_operation(operation_type, details=None):
    """
    Registra un'operazione di database nel log.
    
    Args:
        operation_type (str): Tipo di operazione (select, insert, update, delete)
        details (dict): Dettagli aggiuntivi sull'operazione
    """
    log_data = {
        "operation_type": operation_type,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    
    logger.info(f"DB Operation: {json.dumps(log_data, default=str)}")
