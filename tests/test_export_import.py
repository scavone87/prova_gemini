"""
Script di test per verificare la funzionalità di export/import completo dei funnel.
"""

import json
import logging
import sys
from pathlib import Path

from utils.export_import import export_funnel_config, import_funnel_config

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_export_import(funnel_id, update_existing=True):
    """
    Testa l'esportazione e l'importazione di un funnel.

    Args:
        funnel_id (int): ID del funnel da testare
        update_existing (bool): Se True, aggiorna il funnel esistente
    """
    logger.info(f"Inizio test export/import per funnel ID: {funnel_id}")

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

    # Modifica alcuni dati per verificare l'aggiornamento
    # Ad esempio, modifichiamo il nome del funnel
    export_data["funnel"]["name"] = f"{export_data['funnel']['name']} - Modificato"

    # Se ci sono dati di design, modifichiamo qualcosa
    if "design" in export_data and export_data["design"].get("structures"):
        # Modifica la prima struttura se presente
        structures = export_data["design"]["structures"]
        if structures:
            # Aggiungiamo un campo di test alla prima struttura
            structures[0]["data"]["test_update"] = "Questo è un test di aggiornamento"
            logger.info("Modificata una struttura di design per il test")

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

        test_export_import(funnel_id, update_existing)
    else:
        logger.error("Specificare l'ID del funnel come argomento")
        print("Uso: python test_export_import.py <funnel_id> [update_existing]")
        sys.exit(1)
