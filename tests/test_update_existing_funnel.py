"""
Script di test per verificare l'aggiornamento di funnel esistenti.
"""

import json
import logging
import sys
from pathlib import Path

from utils.export_import import export_funnel_config, import_funnel_config

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_update_existing_funnel(funnel_id, update_existing=True):
    """
    Testa l'aggiornamento di un funnel esistente.

    Args:
        funnel_id (int): ID del funnel da testare
        update_existing (bool): Se True, aggiorna il funnel esistente
    """
    logger.info(f"Inizio test aggiornamento funnel esistente per funnel ID: {funnel_id}")

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

    # Modifica il nome del funnel
    original_name = export_data["funnel"]["name"]
    export_data["funnel"]["name"] = f"{original_name} - Modificato"

    # Salva le modifiche in un nuovo file
    modified_file = test_dir / f"temp_funnel_{funnel_id}_modified.json"
    with open(modified_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Funnel modificato e salvato in {modified_file}")

    # Importa il funnel modificato
    logger.info(f"Importazione del funnel modificato con update_existing={update_existing}...")
    import_result = import_funnel_config(export_data, update_existing)

    if import_result.get("error", True):
        logger.error(f"Errore nell'importazione: {import_result.get('message')}")
        return False

    logger.info("Risultato dell'importazione:")
    logger.info(f"- Messaggio: {import_result.get('message')}")
    logger.info(f"- Funnel ID: {import_result.get('funnel_id')}")
    logger.info(f"- Step importati: {import_result.get('steps_imported')}")
    logger.info(f"- Route importate: {import_result.get('routes_imported')}")

    # Verifica che il funnel sia stato aggiornato e non creato nuovo
    if import_result.get("funnel_id") == funnel_id:
        logger.info("✅ Test superato: il funnel esistente è stato aggiornato correttamente")
    else:
        logger.error(f"❌ Test fallito: è stato creato un nuovo funnel con ID {import_result.get('funnel_id')} invece di aggiornare il funnel esistente con ID {funnel_id}")
        return False

    # Esporta nuovamente il funnel per verificare che il nome sia stato aggiornato
    logger.info("Esportazione del funnel aggiornato per verifica...")
    export_result = export_funnel_config(funnel_id)

    if export_result.get("error", True):
        logger.error(f"Errore nell'esportazione: {export_result.get('message')}")
        return False

    updated_data = export_result["data"]
    updated_name = updated_data["funnel"]["name"]

    if updated_name == f"{original_name} - Modificato":
        logger.info(f"✅ Test superato: il nome del funnel è stato aggiornato correttamente da '{original_name}' a '{updated_name}'")
    else:
        logger.error(f"❌ Test fallito: il nome del funnel non è stato aggiornato correttamente. Atteso: '{original_name} - Modificato', Trovato: '{updated_name}'")
        return False

    logger.info("Test completato con successo!")
    return True

if __name__ == "__main__":
    # Verifica se è stato fornito un ID funnel come argomento
    if len(sys.argv) > 1:
        funnel_id = int(sys.argv[1])
        update_existing = True
        if len(sys.argv) > 2:
            update_existing = sys.argv[2].lower() in ("true", "t", "1", "yes", "y")

        test_update_existing_funnel(funnel_id, update_existing)
    else:
        logger.error("Specificare l'ID del funnel come argomento")
        print("Uso: python test_update_existing_funnel.py <funnel_id> [update_existing]")
        sys.exit(1)
