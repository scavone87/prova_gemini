"""
Componente editor JSON avanzato con validazione e suggerimenti.
Fornisce un'interfaccia migliorata per la modifica di dati JSON all'interno dell'applicazione.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional, Callable, List, Tuple
import re

# Schema di esempio per i tipi di componenti più comuni
DEFAULT_SCHEMAS = {
    "banner": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "subtitle": {"type": "string"},
            "imageUrl": {"type": "string"},
            "buttonText": {"type": "string"},
            "buttonUrl": {"type": "string"}
        }
    },
    "form": {
        "type": "object",
        "properties": {
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "label": {"type": "string"},
                        "type": {"type": "string", "enum": ["text", "number", "select", "checkbox", "date"]},
                        "required": {"type": "boolean"},
                        "options": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            },
            "submitButton": {"type": "string"}
        }
    },
    "text": {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "style": {"type": "object"}
        }
    },
    "image": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "alt": {"type": "string"},
            "caption": {"type": "string"}
        }
    }
}

def validate_json(json_str: str) -> Tuple[bool, str]:
    """
    Valida una stringa JSON e restituisce il risultato della validazione.
    
    Args:
        json_str: La stringa JSON da validare
    
    Returns:
        Tuple con (successo, messaggio_errore)
    """
    if not json_str.strip():
        return False, "Il JSON non può essere vuoto"
    
    try:
        json.loads(json_str)
        return True, ""
    except json.JSONDecodeError as e:
        # Estrai il messaggio di errore e la posizione
        error_msg = str(e)
        line_match = re.search(r'line (\d+)', error_msg)
        col_match = re.search(r'column (\d+)', error_msg)
        
        if line_match and col_match:
            line = int(line_match.group(1))
            col = int(col_match.group(1))
            return False, f"Errore JSON alla linea {line}, colonna {col}: {e.msg}"
        return False, f"Errore JSON: {e.msg}"

def json_editor(
    key: str, 
    default_value: dict = None, 
    height: int = 200,
    component_type: str = None,
    on_change: Optional[Callable] = None
) -> Tuple[bool, Any, str]:
    """
    Editor JSON avanzato con validazione e suggerimenti.
    
    Args:
        key: Chiave univoca per il componente
        default_value: Valore JSON predefinito (dict o None)
        height: Altezza dell'editor in pixel
        component_type: Tipo di componente per suggerimenti di schema
        on_change: Funzione da chiamare quando il valore cambia
    
    Returns:
        Tuple con (valido, valore_json_parsed, errore)
    """
    # Inizializza il valore di default
    if default_value is None:
        if component_type and component_type in DEFAULT_SCHEMAS:
            # Usa lo schema predefinito come template
            default_value = {}
            for prop in DEFAULT_SCHEMAS[component_type]["properties"]:
                if DEFAULT_SCHEMAS[component_type]["properties"][prop]["type"] == "string":
                    default_value[prop] = ""
                elif DEFAULT_SCHEMAS[component_type]["properties"][prop]["type"] == "boolean":
                    default_value[prop] = False
                elif DEFAULT_SCHEMAS[component_type]["properties"][prop]["type"] == "array":
                    default_value[prop] = []
                elif DEFAULT_SCHEMAS[component_type]["properties"][prop]["type"] == "object":
                    default_value[prop] = {}
        else:
            default_value = {}
    
    # Converti il valore predefinito in stringa JSON
    default_json_str = json.dumps(default_value, indent=2)
    
    # Crea una chiave sessionstate per l'editor
    editor_key = f"json_editor_{key}"
    validator_key = f"json_validator_{key}"
    
    # Inizializza lo stato dell'editor
    if editor_key not in st.session_state:
        st.session_state[editor_key] = default_json_str
    
    # Callback per la validazione
    def validate_callback():
        json_str = st.session_state[editor_key]
        is_valid, error = validate_json(json_str)
        st.session_state[validator_key] = (is_valid, error)
        if is_valid and on_change:
            on_change(json.loads(json_str))
    
    # Esempio di schema se disponibile
    if component_type and component_type in DEFAULT_SCHEMAS:
        with st.expander("Schema di esempio"):
            st.code(json.dumps(DEFAULT_SCHEMAS[component_type], indent=2), language="json")
    
    # Editor JSON
    st.text_area(
        "Editor JSON:", 
        st.session_state[editor_key],
        height=height, 
        key=editor_key,
        on_change=validate_callback
    )
    
    # Validazione e suggerimenti
    if validator_key not in st.session_state:
        is_valid, error = validate_json(st.session_state[editor_key])
        st.session_state[validator_key] = (is_valid, error)
    else:
        is_valid, error = st.session_state[validator_key]
    
    # Mostra errori o conferma
    if not is_valid:
        st.error(error)
        return False, None, error
    else:
        st.success("JSON valido ✓")
        try:
            parsed_value = json.loads(st.session_state[editor_key])
            return True, parsed_value, ""
        except:
            return False, None, "Errore durante il parsing del JSON"

def get_component_schema_names() -> List[str]:
    """Restituisce i nomi degli schemi disponibili"""
    return list(DEFAULT_SCHEMAS.keys())