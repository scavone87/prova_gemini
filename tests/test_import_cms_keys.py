"""
Script di test per verificare la gestione delle chiavi CMS durante l'importazione.
"""

import json
import logging
import sys
from pathlib import Path

from utils.export_import import export_funnel_config, import_funnel_config

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_import_cms_keys(funnel_id, update_existing=True):
    """
    Testa l'importazione di un funnel con chiavi CMS.

    Args:
        funnel_id (int): ID del funnel da testare
        update_existing (bool): Se True, aggiorna il funnel esistente
    """
    logger.info(f"Inizio test import con chiavi CMS per funnel ID: {funnel_id}")

    # Esporta il funnel
    logger.info("Esportazione del funnel...")
    export_result = export_funnel_config(funnel_id)

    if export_result.get("error", True):
        logger.error(f"Errore nell'esportazione: {export_result.get('message')}")
        return False

    # Salva il JSON esportato in un file temporaneo
    export_data = export_result["data"]
    test_dir = Path("tests/test_results")
    test_dir.mkdir(exist_ok=True)
    temp_file = test_dir / f"temp_funnel_{funnel_id}.json"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Funnel esportato e salvato in {temp_file}")

    # Modifica il funnel per aggiungere una chiave CMS con valore lista
    design_data = export_data.get("design", {})
    cms_keys = design_data.get("cms_keys", [])

    if cms_keys:
        # Prendi la prima chiave CMS e crea un duplicato con valore lista
        original_key = cms_keys[0]
        duplicate_key = original_key.copy()
        duplicate_key["id"] = max([k["id"] for k in cms_keys]) + 1 if cms_keys else 1
        duplicate_key["value"] = [
            {"key": "test_key_1", "value": "test_value_1"},
            {"key": "test_key_2", "value": "test_value_2"}
        ]

        # Aggiungi il duplicato alla lista delle chiavi CMS
        cms_keys.append(duplicate_key)

        logger.info(f"Aggiunta chiave CMS con valore lista: {duplicate_key}")
    else:
        logger.warning("Il funnel non ha chiavi CMS, impossibile testare la gestione delle chiavi CMS")
        return False

    # Salva le modifiche in un nuovo file
    modified_file = test_dir / f"temp_funnel_{funnel_id}_with_cms_keys.json"
    with open(modified_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Funnel modificato e salvato in {modified_file}")

    # Importa il funnel modificato
    logger.info(f"Importazione del funnel con chiavi CMS con update_existing={update_existing}...")
    import_result = import_funnel_config(export_data, update_existing)

    if import_result.get("error", True):
        logger.error(f"Errore nell'importazione: {import_result.get('message')}")
        return False

    logger.info("Risultato dell'importazione:")
    logger.info(f"- Messaggio: {import_result.get('message')}")
    logger.info(f"- Funnel ID: {import_result.get('funnel_id')}")
    logger.info(f"- Step importati: {import_result.get('steps_imported')}")
    logger.info(f"- Route importate: {import_result.get('routes_imported')}")

    design_imported = import_result.get("design_imported")
    if design_imported:
        logger.info("Dati di design importati:")
        logger.info(f"- Sezioni: {design_imported.get('sections', 0)}")
        logger.info(f"- Componenti: {design_imported.get('components', 0)}")
        logger.info(f"- Strutture: {design_imported.get('structures', 0)}")
        logger.info(f"- Chiavi CMS: {design_imported.get('cms_keys', 0)}")

    logger.info("Test completato con successo!")
    return True

if __name__ == "__main__":
    # Verifica se è stato fornito un ID funnel come argomento
    if len(sys.argv) > 1:
        funnel_id = int(sys.argv[1])
        update_existing = True
        if len(sys.argv) > 2:
            update_existing = sys.argv[2].lower() in ("true", "t", "1", "yes", "y")

        test_import_cms_keys(funnel_id, update_existing)
    else:
        logger.error("Specificare l'ID del funnel come argomento")
        print("Uso: python test_import_cms_keys.py <funnel_id> [update_existing]")
        sys.exit(1)
