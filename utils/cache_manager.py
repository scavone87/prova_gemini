"""
Modulo per la gestione centralizzata delle funzionalità di cache dell'applicazione.

Questo modulo fornisce funzioni per la gestione efficiente della cache per diverse 
parti dell'applicazione, facilitando la gestione dei tempi di vita (TTL) e delle 
strategie di invalidazione della cache.
"""

import streamlit as st
import logging
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast, Union

# Configurazione del logging
logger = logging.getLogger(__name__)

# Definizione di tipi generici per le funzioni
T = TypeVar('T')
CacheableFunction = Callable[..., T]

def cached_function(ttl: int = 3600) -> Callable[[CacheableFunction], CacheableFunction]:
    """
    Decoratore per cachare il risultato di una funzione con possibilità di invalidazione.
    
    Questa funzione crea un decoratore che avvolge una funzione target e cachea il suo output
    per un periodo specifico. Utilizza st.cache_data di Streamlit internamente ma aggiunge
    la capacità di invalidare selettivamente la cache in base a condizioni definite nella 
    session_state.
    
    Args:
        ttl (int, optional): Tempo di vita della cache in secondi. Default: 3600 (1 ora).
    
    Returns:
        Callable: Un decoratore che può essere applicato a una funzione.
    
    Example:
        ```
        @cached_function(ttl=600)
        def get_expensive_data(param1, param2):
            # Codice che richiede tempo di esecuzione
            return data
        ```
    """
    def decorator(func: CacheableFunction) -> CacheableFunction:
        # Nome univoco per la funzione
        func_name = func.__name__
        
        # Utilizziamo st.cache_data come decoratore di base
        # ma aggiungiamo la nostra logica per l'invalidazione
        cached_func = st.cache_data(ttl=ttl)(func)
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Controlla se dobbiamo invalidare la cache
            invalidate_key = f"invalidate_{func_name}_cache"
            
            if invalidate_key in st.session_state and st.session_state[invalidate_key]:
                logger.info(f"Invalidazione cache per {func_name}")
                cached_func.clear()
                st.session_state[invalidate_key] = False
            
            # Chiama la funzione con cache
            return cached_func(*args, **kwargs)
        
        return cast(CacheableFunction, wrapper)
    
    return decorator

def invalidate_cache(func_name: str) -> None:
    """
    Imposta un flag per invalidare la cache di una funzione specifica.
    
    Args:
        func_name (str): Nome della funzione la cui cache deve essere invalidata
    """
    invalidate_key = f"invalidate_{func_name}_cache"
    st.session_state[invalidate_key] = True
    logger.debug(f"Flag di invalidazione cache impostato per {func_name}")

def invalidate_all_caches() -> None:
    """
    Invalida tutte le cache note dell'applicazione.
    """
    # Cerca tutti i flag di invalidazione nella session_state
    for key in list(st.session_state.keys()):
        if key.startswith("invalidate_") and key.endswith("_cache"):
            st.session_state[key] = True
    
    logger.info("Invalidazione di tutte le cache richiesta")

def register_cache_clear_handlers() -> None:
    """
    Registra gestori di invalidazione cache per eventi comuni.
    
    Questa funzione configura handlers automatici per invalidare le cache
    in risposta a determinati eventi dell'applicazione.
    """
    # Questo è solo un esempio. Nella pratica, dovresti definire
    # i gestori specifici necessari per la tua applicazione.
    
    # Esempio: invalidare le cache pertinenti quando viene creato un nuovo step
    if 'step_created' in st.session_state and st.session_state.step_created:
        invalidate_cache("get_steps")
        invalidate_cache("get_steps_for_workflow")
        st.session_state.step_created = False
    
    # Esempio: invalidare le cache pertinenti quando viene creata una nuova route
    if 'route_created' in st.session_state and st.session_state.route_created:
        invalidate_cache("get_routes")
        invalidate_cache("get_routes_for_workflow")
        st.session_state.route_created = False

def cache_stats() -> Dict[str, Any]:
    """
    Raccoglie e restituisce statistiche sulla cache.
    
    Returns:
        Dict[str, Any]: Un dizionario con informazioni sulle cache attive
    """
    # Streamlit non fornisce un API diretto per accedere alle statistiche della cache,
    # quindi questa è un'implementazione simulata.
    # In un'implementazione reale, dovresti utilizzare il meccanismo specifico
    # della tua strategia di caching.
    
    # Esempio di statistiche simulate
    return {
        "active_caches": len([k for k in st.session_state.keys() if k.startswith("invalidate_")]),
        "last_invalidation": st.session_state.get("last_cache_invalidation", "mai"),
    }