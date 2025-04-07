"""
Modulo per la gestione centralizzata degli errori e del logging.

Fornisce funzioni per gestire errori in modo coerente e per
registrare eventi significativi nell'applicazione.
"""

import functools
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

# Configurazione del logger
logger = logging.getLogger(__name__)

# Costanti per livelli di gravità personalizzati
ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"
DEBUG = "DEBUG"


class AppError(Exception):
    """Classe base personalizzata per le eccezioni dell'applicazione."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(message)


class ValidationError(AppError):
    """Eccezione sollevata quando i dati di input non sono validi."""

    pass


class DatabaseError(AppError):
    """Eccezione sollevata per problemi relativi al database."""

    pass


class ConfigurationError(AppError):
    """Eccezione sollevata per problemi di configurazione."""

    pass


class NotFoundError(AppError):
    """Eccezione sollevata quando una risorsa richiesta non viene trovata."""

    pass


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_rotation: bool = True,
    log_format: Optional[str] = None,
) -> None:
    """
    Configurazione del sistema di logging.

    Args:
        log_level: Livello di log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Percorso del file di log (opzionale)
        log_rotation: Se True, abilita la rotazione dei file di log
        log_format: Formato personalizzato per i messaggi di log
    """
    # Converti la stringa del livello di log in costante
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Formato di default per i log
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configurazione di base
    logging_config = {
        "level": numeric_level,
        "format": log_format,
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }

    # Se è specificato un file di log
    if log_file:
        if log_rotation:
            # Usa un RotatingFileHandler per la rotazione dei log
            from logging.handlers import RotatingFileHandler

            # Crea la directory per il file di log se non esiste
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

            # Configura il handler con rotazione (max 5MB, max 5 file)
            handler = RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
            )
            handler.setFormatter(logging.Formatter(log_format))

            # Aggiungi il handler al logger root
            root_logger = logging.getLogger()
            root_logger.setLevel(numeric_level)
            root_logger.addHandler(handler)

            # Aggiungi anche un handler per la console
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(log_format))
            root_logger.addHandler(console_handler)
        else:
            # Usa logging.basicConfig con il file specificato
            logging_config["filename"] = log_file
            logging_config["filemode"] = "a"  # append mode
            logging.basicConfig(**logging_config)
    else:
        # Configurazione di base solo per la console
        logging.basicConfig(**logging_config)

    # Log iniziale per confermare la configurazione
    logger.info(f"Logging configurato con livello {log_level}")

    # Imposta il livello di logging anche per le librerie più comuni
    logging.getLogger("sqlalchemy").setLevel(max(numeric_level, logging.WARNING))
    logging.getLogger("urllib3").setLevel(max(numeric_level, logging.WARNING))
    logging.getLogger("streamlit").setLevel(max(numeric_level, logging.INFO))


def handle_error(
    exception: Exception, message: Optional[str] = None, fallback_data: Any = None
) -> Dict[str, Any]:
    """
    Gestisce un'eccezione in modo standardizzato e torna una risposta consistente.

    Args:
        exception: L'eccezione catturata
        message: Messaggio d'errore personalizzato (usa exception.__str__() se None)
        fallback_data: Dati da restituire in caso di errore

    Returns:
        Dict con i dettagli dell'errore e i dati predefiniti
    """
    # Estrai il messaggio dall'eccezione se non specificato
    error_message = message or str(exception)

    # Ottieni lo stack trace
    exc_type, exc_value, exc_traceback = sys.exc_info()
    stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)

    # Normalizza il tipo di eccezione
    exception_type = exception.__class__.__name__

    # Log dell'errore
    logger.error(f"ERROR [{exception_type}]: {error_message}", exc_info=True)

    # Prepara la risposta
    error_details = {
        "error": True,
        "message": error_message,
        "type": exception_type,
        "timestamp": datetime.now().isoformat(),
    }

    # In modalità debug, includi lo stack trace
    if os.environ.get("APP_ENV") != "production":
        error_details["stack_trace"] = "".join(stack_trace)

    # Se è specificato un fallback_data, restituiscilo
    if fallback_data is not None:
        error_details["data"] = fallback_data

    return error_details


def log_operation(
    operation: str, data: Optional[Dict[str, Any]] = None, level: int = logging.INFO
) -> None:
    """
    Registra un'operazione nel log.

    Args:
        operation: Nome dell'operazione eseguita
        data: Dati associati all'operazione (opzionale)
        level: Livello di logging da usare
    """
    # Prepara il messaggio di log
    log_data = {
        "operation": operation,
        "timestamp": datetime.now().isoformat(),
    }

    # Aggiungi i dati se presenti
    if data:
        log_data["data"] = data

    # Log dell'operazione
    logger.log(level, f"OPERATION: {operation} - {json.dumps(log_data, default=str)}")


def error_boundary(fallback_value: Any = None) -> Callable:
    """
    Decoratore che cattura le eccezioni in una funzione e restituisce un valore predefinito.

    Args:
        fallback_value: Valore da restituire in caso di eccezione

    Returns:
        Decoratore per gestire le eccezioni
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Gestisci l'errore
                handle_error(e, f"Error in {func.__name__}", fallback_value)
                # Restituisci il valore predefinito
                return fallback_value

        return wrapper

    return decorator
