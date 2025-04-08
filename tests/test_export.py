"""
Script di test per verificare la funzionalità di export dei funnel.
"""

import json
import logging
import sys
from pathlib import Path

from utils.export_import import export_funnel_config

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_export(funnel_id):
    """
    Testa l'esportazione di un funnel.

    Args:
        funnel_id (int): ID del funnel da testare
    """
    logger.info(f"Inizio test export per funnel ID: {funnel_id}")

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

    # Verifica che ci siano dati di design
    design_data = export_data.get("design", {})
    sections = design_data.get("sections", [])
    components = design_data.get("components", [])
    structures = design_data.get("structures", [])
    cms_keys = design_data.get("cms_keys", [])

    logger.info("Dati di design esportati:")
    logger.info(f"- Sezioni: {len(sections)}")
    logger.info(f"- Componenti: {len(components)}")
    logger.info(f"- Strutture: {len(structures)}")
    logger.info(f"- Chiavi CMS: {len(cms_keys)}")

    logger.info("Test completato con successo!")
    return True

if __name__ == "__main__":
    # Verifica se è stato fornito un ID funnel come argomento
    if len(sys.argv) > 1:
        funnel_id = int(sys.argv[1])
        test_export(funnel_id)
    else:
        logger.error("Specificare l'ID del funnel come argomento")
        print("Uso: python test_export.py <funnel_id>")
        sys.exit(1)
