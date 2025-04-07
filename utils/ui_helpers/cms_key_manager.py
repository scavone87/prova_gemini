"""
Modulo di gestione CMS Key - Fornisce un'interfaccia form-based per la gestione delle CMS key
invece dell'editor JSON grezzo, rendendo il processo più user-friendly.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional, List, Tuple, Callable

# Tipi comuni di CMS Key con template predefiniti
CMS_KEY_TEMPLATES = {
    "text": {
        "it": "",
        "en": ""
    },
    "image": {
        "url": "",
        "alt": {
            "it": "",
            "en": ""
        }
    },
    "link": {
        "url": "",
        "text": {
            "it": "",
            "en": ""
        },
        "target": "_blank"
    },
    "button": {
        "url": "",
        "label": {
            "it": "",
            "en": ""
        },
        "style": "primary"
    }
}

def cms_key_form(
    key: str, 
    default_value: Dict = None, 
    template_type: str = None,
    on_change: Optional[Callable] = None
) -> Tuple[bool, Dict, str]:
    """
    Form per la gestione delle CMS Key basato sul tipo selezionato.
    
    Args:
        key: Chiave univoca per il componente
        default_value: Valore predefinito delle CMS Key (dict)
        template_type: Tipo di template da utilizzare (text, image, link, button, custom)
        on_change: Funzione callback da chiamare quando il valore cambia
        
    Returns:
        Tuple con (modificato, valore_cms_key, errore)
    """
    form_key = f"cms_key_form_{key}"
    data_key = f"cms_key_data_{key}"
    template_key = f"cms_key_template_{key}"
    
    # Inizializza lo stato se necessario
    if data_key not in st.session_state:
        if default_value:
            st.session_state[data_key] = default_value
        elif template_type and template_type in CMS_KEY_TEMPLATES:
            st.session_state[data_key] = CMS_KEY_TEMPLATES[template_type].copy()
        else:
            st.session_state[data_key] = {}
    
    if template_key not in st.session_state:
        st.session_state[template_key] = template_type if template_type else "custom"
    
    # Form per la gestione della CMS Key
    with st.expander("CMS Key Editor", expanded=True):
        # Selezione del template
        template_options = list(CMS_KEY_TEMPLATES.keys()) + ["custom"]
        selected_template = st.selectbox(
            "Tipo di CMS Key:", 
            template_options,
            index=template_options.index(st.session_state[template_key]) if st.session_state[template_key] in template_options else len(template_options) - 1,
            key=f"{template_key}_select"
        )
        
        # Se cambia il template, aggiorna i dati
        if selected_template != st.session_state[template_key] and selected_template != "custom":
            st.session_state[data_key] = CMS_KEY_TEMPLATES[selected_template].copy()
            st.session_state[template_key] = selected_template
        
        # Form dinamico basato sul template selezionato
        with st.form(key=form_key):
            modified = False
            current_data = st.session_state[data_key].copy()
            
            if selected_template == "text":
                _render_text_form(current_data)
            elif selected_template == "image":
                _render_image_form(current_data)
            elif selected_template == "link":
                _render_link_form(current_data)
            elif selected_template == "button":
                _render_button_form(current_data)
            else:  # custom
                _render_custom_form(current_data)
            
            # Pulsanti di salvataggio
            if st.form_submit_button("Salva CMS Key"):
                st.session_state[data_key] = current_data
                modified = True
                if on_change:
                    on_change(current_data)
            
            # Visualizza il JSON corrente
            with st.expander("Visualizza JSON", expanded=False):
                st.code(json.dumps(st.session_state[data_key], indent=2), language="json")
                
            return modified, st.session_state[data_key], ""

def _render_text_form(data: Dict):
    """Renderizza il form per il template di tipo 'text'"""
    if "it" in data:
        data["it"] = st.text_area("Testo (Italiano):", value=data.get("it", ""))
    else:
        data["it"] = st.text_area("Testo (Italiano):", value="")
        
    if "en" in data:
        data["en"] = st.text_area("Testo (Inglese):", value=data.get("en", ""))
    else:
        data["en"] = st.text_area("Testo (Inglese):", value="")

def _render_image_form(data: Dict):
    """Renderizza il form per il template di tipo 'image'"""
    data["url"] = st.text_input("URL Immagine:", value=data.get("url", ""))
    
    if "alt" not in data:
        data["alt"] = {}
    
    alt = data["alt"]
    if isinstance(alt, dict):
        alt["it"] = st.text_input("Testo alternativo (Italiano):", value=alt.get("it", ""))
        alt["en"] = st.text_input("Testo alternativo (Inglese):", value=alt.get("en", ""))
    else:
        # Gestisce il caso in cui alt non è un dizionario
        new_alt = {
            "it": st.text_input("Testo alternativo (Italiano):", value=""),
            "en": st.text_input("Testo alternativo (Inglese):", value="")
        }
        data["alt"] = new_alt

def _render_link_form(data: Dict):
    """Renderizza il form per il template di tipo 'link'"""
    data["url"] = st.text_input("URL Link:", value=data.get("url", ""))
    
    if "text" not in data:
        data["text"] = {}
    
    text = data["text"]
    if isinstance(text, dict):
        text["it"] = st.text_input("Testo link (Italiano):", value=text.get("it", ""))
        text["en"] = st.text_input("Testo link (Inglese):", value=text.get("en", ""))
    else:
        # Gestisce il caso in cui text non è un dizionario
        new_text = {
            "it": st.text_input("Testo link (Italiano):", value=""),
            "en": st.text_input("Testo link (Inglese):", value="")
        }
        data["text"] = new_text
    
    data["target"] = st.selectbox(
        "Target:", 
        ["_self", "_blank", "_parent", "_top"], 
        index=["_self", "_blank", "_parent", "_top"].index(data.get("target", "_blank"))
    )

def _render_button_form(data: Dict):
    """Renderizza il form per il template di tipo 'button'"""
    data["url"] = st.text_input("URL Pulsante:", value=data.get("url", ""))
    
    if "label" not in data:
        data["label"] = {}
    
    label = data["label"]
    if isinstance(label, dict):
        label["it"] = st.text_input("Etichetta pulsante (Italiano):", value=label.get("it", ""))
        label["en"] = st.text_input("Etichetta pulsante (Inglese):", value=label.get("en", ""))
    else:
        # Gestisce il caso in cui label non è un dizionario
        new_label = {
            "it": st.text_input("Etichetta pulsante (Italiano):", value=""),
            "en": st.text_input("Etichetta pulsante (Inglese):", value="")
        }
        data["label"] = new_label
    
    data["style"] = st.selectbox(
        "Stile:", 
        ["primary", "secondary", "outline", "link"],
        index=["primary", "secondary", "outline", "link"].index(data.get("style", "primary"))
    )

def _render_custom_form(data: Dict):
    """Renderizza il form per il template personalizzato"""
    # In questo caso mostriamo un editor JSON testuale
    json_str = st.text_area("JSON CMS Key:", value=json.dumps(data, indent=2), height=300)
    try:
        parsed_data = json.loads(json_str)
        # Aggiorna tutti i campi con i valori dal JSON
        data.clear()
        data.update(parsed_data)
    except json.JSONDecodeError:
        st.error("JSON non valido. Verifica la sintassi.")

def get_cms_key_templates() -> List[str]:
    """Restituisce i nomi dei template CMS Key disponibili"""
    return list(CMS_KEY_TEMPLATES.keys()) + ["custom"]