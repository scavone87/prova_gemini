"""
Modulo per la gestione centralizzata della configurazione dell'applicazione.

Fornisce accesso alle configurazioni dell'applicazione da diverse fonti:
- File di configurazione (.env)
- Streamlit secrets
- Valori di default integrati

Tutte le configurazioni vengono uniformate in un unico dizionario accessibile tramite CONFIG.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
import streamlit as st
from dotenv import load_dotenv

# Configurazione del logging
logger = logging.getLogger(__name__)

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Costanti per le chiavi di configurazione
DB_PREFIX = "DB_"
APP_PREFIX = "APP_"

# Configurazione della pagina Streamlit di default
PAGE_CONFIG = {
    "page_title": "Funnel Manager Dashboard",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Configurazione dell'applicazione di default
APP_CONFIG = {
    "default_broker_id": 1,  # ID del broker di default
    "items_per_page": 10,     # Numero di elementi per pagina nelle liste
    "cache_ttl": 600,         # Durata predefinita della cache in secondi (10 minuti)
    "enable_analytics": False, # Attiva/disattiva analitiche
    "log_level": "INFO",      # Livello di logging predefinito
    "theme": "light",         # Tema dell'interfaccia utente
    "version": "1.2.0",       # Versione dell'applicazione
}

def load_config() -> Dict[str, Any]:
    """
    Carica la configurazione da tutte le fonti disponibili.
    
    L'ordine di precedenza è:
    1. Streamlit secrets
    2. Variabili d'ambiente
    3. Valori predefiniti
    
    Returns:
        Dict[str, Any]: Dizionario con la configurazione completa
    """
    config = APP_CONFIG.copy()
    
    # Carica configurazioni da variabili d'ambiente
    for key, value in os.environ.items():
        if key.startswith(APP_PREFIX):
            # Rimuovi il prefisso e converti in minuscolo
            app_key = key[len(APP_PREFIX):].lower()
            
            # Gestisci i tipi di dati in base al formato
            if value.lower() in ['true', 'yes', '1']:
                config[app_key] = True
            elif value.lower() in ['false', 'no', '0']:
                config[app_key] = False
            elif value.isdigit():
                config[app_key] = int(value)
            elif value.replace('.', '', 1).isdigit():
                config[app_key] = float(value)
            else:
                # Prova a interpretare come JSON se inizia con { o [
                if (value.startswith('{') and value.endswith('}')) or \
                   (value.startswith('[') and value.endswith(']')):
                    try:
                        config[app_key] = json.loads(value)
                    except json.JSONDecodeError:
                        config[app_key] = value
                else:
                    config[app_key] = value
    
    # Carica configurazioni da Streamlit secrets (se disponibili)
    if hasattr(st, 'secrets') and 'app_config' in st.secrets:
        for key, value in st.secrets.app_config.items():
            config[key] = value
    
    # Applica override specifici per l'ambiente
    env = os.environ.get("APP_ENV", "development").lower()
    if env == "production":
        # In produzione, aumenta la durata della cache e disabilita funzioni di debug
        config["cache_ttl"] = max(config.get("cache_ttl", 600), 1800)
        config["debug_mode"] = False
    elif env == "test":
        # In modalità test, riduce la durata della cache e abilita debug
        config["cache_ttl"] = 10
        config["debug_mode"] = True
    
    logger.info(f"Configurazione caricata per l'ambiente: {env}")
    return config

def get_db_config() -> Dict[str, str]:
    """
    Recupera la configurazione del database.
    
    Returns:
        Dict[str, str]: Dizionario con le configurazioni del database
    """
    # Configurazione predefinita
    db_config = {
        "host": "localhost",
        "port": "5432",
        "name": "funnel_manager",
        "user": "postgres",
        "password": "postgres",
    }
    
    # Aggiorna con variabili d'ambiente
    if os.environ.get(f"{DB_PREFIX}HOST"):
        db_config["host"] = os.environ.get(f"{DB_PREFIX}HOST")
    if os.environ.get(f"{DB_PREFIX}PORT"):
        db_config["port"] = os.environ.get(f"{DB_PREFIX}PORT")
    if os.environ.get(f"{DB_PREFIX}NAME"):
        db_config["name"] = os.environ.get(f"{DB_PREFIX}NAME")
    if os.environ.get(f"{DB_PREFIX}USER"):
        db_config["user"] = os.environ.get(f"{DB_PREFIX}USER")
    if os.environ.get(f"{DB_PREFIX}PASSWORD"):
        db_config["password"] = os.environ.get(f"{DB_PREFIX}PASSWORD")
    
    # Aggiorna con Streamlit secrets se disponibili
    if hasattr(st, 'secrets') and 'db' in st.secrets:
        for key in db_config:
            if key in st.secrets.db:
                db_config[key] = st.secrets.db[key]
    
    return db_config

# Carica la configurazione all'avvio
CONFIG = load_config()

def get_config(key: str, default: Any = None) -> Any:
    """
    Recupera un valore di configurazione.
    
    Args:
        key (str): La chiave di configurazione
        default (Any, optional): Valore predefinito se la chiave non esiste
        
    Returns:
        Any: Il valore di configurazione o il default
    """
    return CONFIG.get(key, default)

def set_config(key: str, value: Any) -> None:
    """
    Imposta un valore di configurazione a runtime.
    
    Args:
        key (str): La chiave di configurazione
        value (Any): Il valore da assegnare
    """
    CONFIG[key] = value
    logger.debug(f"Configurazione aggiornata: {key} = {value}")

def get_connection_string() -> str:
    """
    Costruisce e restituisce la stringa di connessione al database.
    
    Returns:
        str: Stringa di connessione al database PostgreSQL
    """
    db_config = get_db_config()
    
    return (
        f"postgresql://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['name']}"
    )