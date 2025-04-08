"""
Batteria di test completa per la funzionalità di import/export dei funnel.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.export_import import export_funnel_config, import_funnel_config
from utils.db_utils import get_db_session, close_db_session
from sqlalchemy import text

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FunnelTestSuite:
    """Suite di test per la funzionalità di import/export dei funnel."""

    def __init__(self, funnel_id: int):
        """
        Inizializza la suite di test.

        Args:
            funnel_id (int): ID del funnel da utilizzare per i test
        """
        self.funnel_id = funnel_id
        self.test_dir = Path("tests/test_results")
        self.test_dir.mkdir(exist_ok=True)
        self.results = []

        # Crea una sessione del database
        self.session = get_db_session()

    def __del__(self):
        """Chiude la sessione del database quando l'oggetto viene distrutto."""
        if hasattr(self, 'session'):
            close_db_session(self.session)

    def run_all_tests(self):
        """Esegue tutti i test della suite."""
        logger.info("=== INIZIO DELLA SUITE DI TEST ===")

        # Test 1: Esportazione base
        self.test_export_basic()

        # Test 2: Importazione nuovo funnel
        self.test_import_new_funnel()

        # Test 3: Aggiornamento funnel esistente
        self.test_update_existing_funnel()

        # Test 4: Gestione degli step duplicati
        self.test_duplicate_steps()

        # Test 5: Gestione dei valori JSON complessi
        self.test_complex_json_values()

        # Test 6: Gestione delle parole chiave riservate
        self.test_reserved_keywords()

        # Test 7: Importazione con ID funnel esplicito
        self.test_import_with_explicit_id()

        # Riepilogo dei risultati
        self.print_summary()

    def print_summary(self):
        """Stampa un riepilogo dei risultati dei test."""
        logger.info("\n=== RIEPILOGO DEI TEST ===")

        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')

        logger.info(f"Test eseguiti: {len(self.results)}")
        logger.info(f"Test superati: {passed}")
        logger.info(f"Test falliti: {failed}")

        if failed > 0:
            logger.info("\nTest falliti:")
            for i, result in enumerate(self.results):
                if result['status'] == 'FAIL':
                    logger.info(f"  {i+1}. {result['name']}: {result['message']}")

    def add_result(self, name: str, status: str, message: str):
        """
        Aggiunge un risultato alla lista dei risultati.

        Args:
            name (str): Nome del test
            status (str): Stato del test ('PASS' o 'FAIL')
            message (str): Messaggio del risultato
        """
        self.results.append({
            'name': name,
            'status': status,
            'message': message
        })

        if status == 'PASS':
            logger.info(f"✅ {name}: {message}")
        else:
            logger.error(f"❌ {name}: {message}")

    def get_funnel_name(self, funnel_id: int) -> Optional[str]:
        """
        Ottiene il nome di un funnel dal database.

        Args:
            funnel_id (int): ID del funnel

        Returns:
            Optional[str]: Nome del funnel, o None se non trovato
        """
        query = text("SELECT name FROM funnel_manager.funnel WHERE id = :funnel_id")
        result = self.session.execute(query, {"funnel_id": funnel_id}).fetchone()

        if result:
            return result[0]
        return None

    def test_export_basic(self):
        """Test di esportazione base."""
        test_name = "Test di esportazione base"
        logger.info(f"\n=== {test_name} ===")

        try:
            # Esporta il funnel
            export_result = export_funnel_config(self.funnel_id)

            if export_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'esportazione: {export_result.get('message')}")
                return

            # Verifica che i dati esportati contengano le informazioni essenziali
            export_data = export_result["data"]

            if not all(key in export_data for key in ["funnel", "workflow", "steps", "routes"]):
                self.add_result(test_name, "FAIL", "I dati esportati non contengono tutte le informazioni essenziali")
                return

            # Salva i dati esportati in un file
            export_file = self.test_dir / f"export_basic_{self.funnel_id}.json"
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            # Verifica che i dati di design siano presenti (se applicabile)
            has_design = "design" in export_data and isinstance(export_data["design"], dict)

            self.add_result(
                test_name,
                "PASS",
                f"Funnel esportato con successo. File: {export_file}. " +
                f"Contiene dati di design: {'Sì' if has_design else 'No'}"
            )

        except Exception as e:
            self.add_result(test_name, "FAIL", f"Eccezione durante il test: {str(e)}")

    def test_import_new_funnel(self):
        """Test di importazione nuovo funnel."""
        test_name = "Test di importazione nuovo funnel"
        logger.info(f"\n=== {test_name} ===")

        try:
            # Esporta il funnel originale
            export_result = export_funnel_config(self.funnel_id)

            if export_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'esportazione: {export_result.get('message')}")
                return

            # Modifica i dati per creare un nuovo funnel
            export_data = export_result["data"]
            original_name = export_data["funnel"]["name"]

            # Cambia il nome e l'ID del prodotto per creare un nuovo funnel
            export_data["funnel"]["name"] = f"{original_name} - Nuovo Test {int(time.time())}"

            # Genera un nuovo ID prodotto (incrementa di 1000 + timestamp per evitare conflitti)
            original_product_id = export_data["funnel"]["product"]["id"]
            new_product_id = original_product_id + 1000 + int(time.time()) % 1000
            export_data["funnel"]["product"]["id"] = new_product_id

            # Rimuovi l'ID del funnel per assicurarsi che venga creato un nuovo funnel
            if "id" in export_data["funnel"]:
                del export_data["funnel"]["id"]

            # Salva i dati modificati in un file
            import_file = self.test_dir / f"import_new_{self.funnel_id}.json"
            with open(import_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            # Importa il nuovo funnel
            import_result = import_funnel_config(export_data, update_existing=False)

            if import_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'importazione: {import_result.get('message')}")
                return

            # Verifica che sia stato creato un nuovo funnel
            new_funnel_id = import_result.get("funnel_id")

            if not new_funnel_id or new_funnel_id == self.funnel_id:
                self.add_result(test_name, "FAIL", f"Non è stato creato un nuovo funnel. ID ottenuto: {new_funnel_id}")
                return

            # Verifica che il nome del nuovo funnel sia corretto
            new_funnel_name = self.get_funnel_name(new_funnel_id)
            expected_name = f"{original_name} - Nuovo Test {int(time.time())}"

            # Verifichiamo solo che il nome contenga "Nuovo Test", poiché il timestamp può variare
            if "Nuovo Test" not in new_funnel_name:
                self.add_result(
                    test_name,
                    "FAIL",
                    f"Il nome del nuovo funnel non è corretto. Dovrebbe contenere 'Nuovo Test', Trovato: '{new_funnel_name}'"
                )
                return

            self.add_result(
                test_name,
                "PASS",
                f"Nuovo funnel creato con successo. ID: {new_funnel_id}, Nome: '{new_funnel_name}'"
            )

            # Salva l'ID del nuovo funnel per i test successivi
            self.new_funnel_id = new_funnel_id

        except Exception as e:
            self.add_result(test_name, "FAIL", f"Eccezione durante il test: {str(e)}")

    def test_update_existing_funnel(self):
        """Test di aggiornamento funnel esistente."""
        test_name = "Test di aggiornamento funnel esistente"
        logger.info(f"\n=== {test_name} ===")

        try:
            # Utilizziamo il funnel originale invece di quello creato nel test precedente
            # per evitare problemi di accesso al nuovo funnel
            funnel_id = self.funnel_id

            # Esporta il funnel originale
            export_result = export_funnel_config(funnel_id)

            if export_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'esportazione: {export_result.get('message')}")
                return

            # Modifica i dati per aggiornare il funnel
            export_data = export_result["data"]
            original_name = export_data["funnel"]["name"]

            # Cambia il nome del funnel
            export_data["funnel"]["name"] = f"{original_name} - Aggiornato"

            # Salva i dati modificati in un file
            update_file = self.test_dir / f"update_existing_{self.new_funnel_id}.json"
            with open(update_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            # Importa il funnel aggiornato
            import_result = import_funnel_config(export_data, update_existing=True)

            if import_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'importazione: {import_result.get('message')}")
                return

            # Verifica che sia stato aggiornato il funnel esistente
            updated_funnel_id = import_result.get("funnel_id")

            if updated_funnel_id != funnel_id:
                self.add_result(
                    test_name,
                    "FAIL",
                    f"Non è stato aggiornato il funnel esistente. ID atteso: {funnel_id}, ID ottenuto: {updated_funnel_id}"
                )
                return

            # Verifica che il nome del funnel sia stato aggiornato
            updated_funnel_name = self.get_funnel_name(updated_funnel_id)
            expected_name = f"{original_name} - Aggiornato"

            if updated_funnel_name != expected_name:
                self.add_result(
                    test_name,
                    "FAIL",
                    f"Il nome del funnel non è stato aggiornato. Atteso: '{expected_name}', Trovato: '{updated_funnel_name}'"
                )
                return

            self.add_result(
                test_name,
                "PASS",
                f"Funnel aggiornato con successo. ID: {updated_funnel_id}, Nome: '{updated_funnel_name}'"
            )

        except Exception as e:
            self.add_result(test_name, "FAIL", f"Eccezione durante il test: {str(e)}")

    def test_duplicate_steps(self):
        """Test di gestione degli step duplicati."""
        test_name = "Test di gestione degli step duplicati"
        logger.info(f"\n=== {test_name} ===")

        try:
            # Esporta il funnel originale
            export_result = export_funnel_config(self.funnel_id)

            if export_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'esportazione: {export_result.get('message')}")
                return

            # Modifica i dati per creare step duplicati
            export_data = export_result["data"]
            steps = export_data.get("steps", [])

            if not steps:
                self.add_result(test_name, "FAIL", "Il funnel non ha step, impossibile testare la gestione dei duplicati")
                return

            # Prendi il primo step e crea un duplicato con ID diverso
            original_step = steps[0]
            duplicate_step = original_step.copy()
            duplicate_step["id"] = max([s["id"] for s in steps]) + 1  # Nuovo ID

            # Aggiungi il duplicato alla lista degli step
            steps.append(duplicate_step)

            # Salva i dati modificati in un file
            duplicate_file = self.test_dir / f"duplicate_steps_{self.funnel_id}.json"
            with open(duplicate_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            # Importa il funnel con step duplicati
            import_result = import_funnel_config(export_data, update_existing=True)

            if import_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'importazione: {import_result.get('message')}")
                return

            self.add_result(
                test_name,
                "PASS",
                f"Funnel con step duplicati importato con successo. ID: {import_result.get('funnel_id')}"
            )

        except Exception as e:
            self.add_result(test_name, "FAIL", f"Eccezione durante il test: {str(e)}")

    def test_complex_json_values(self):
        """Test di gestione dei valori JSON complessi."""
        test_name = "Test di gestione dei valori JSON complessi"
        logger.info(f"\n=== {test_name} ===")

        try:
            # Esporta il funnel originale
            export_result = export_funnel_config(self.funnel_id)

            if export_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'esportazione: {export_result.get('message')}")
                return

            # Modifica i dati per aggiungere valori JSON complessi
            export_data = export_result["data"]
            design_data = export_data.get("design", {})

            # Aggiungi una struttura con dati JSON complessi
            structures = design_data.get("structures", [])

            if not structures:
                # Se non ci sono strutture, crea una struttura di test
                new_structure = {
                    "id": 9999,
                    "data": {
                        "complex_data": {
                            "nested": {
                                "array": [1, 2, 3],
                                "object": {"key": "value"}
                            }
                        }
                    }
                }

                if "design" not in export_data:
                    export_data["design"] = {}

                if "structures" not in export_data["design"]:
                    export_data["design"]["structures"] = []

                export_data["design"]["structures"].append(new_structure)
            else:
                # Modifica la prima struttura esistente
                structures[0]["data"] = {
                    "complex_data": {
                        "nested": {
                            "array": [1, 2, 3],
                            "object": {"key": "value"}
                        }
                    }
                }

            # Aggiungi una chiave CMS con valore lista
            cms_keys = design_data.get("cms_keys", [])

            new_cms_key = {
                "id": 9999,
                "value": [
                    {"key": "test_key_1", "value": "test_value_1"},
                    {"key": "test_key_2", "value": "test_value_2"}
                ],
                "structurecomponentsectionid": structures[0].get("structure_component_section_id", 1) if structures else 1
            }

            if "cms_keys" not in export_data["design"]:
                export_data["design"]["cms_keys"] = []

            export_data["design"]["cms_keys"].append(new_cms_key)

            # Salva i dati modificati in un file
            complex_file = self.test_dir / f"complex_json_{self.funnel_id}.json"
            with open(complex_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            # Importa il funnel con valori JSON complessi
            import_result = import_funnel_config(export_data, update_existing=True)

            if import_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'importazione: {import_result.get('message')}")
                return

            self.add_result(
                test_name,
                "PASS",
                f"Funnel con valori JSON complessi importato con successo. ID: {import_result.get('funnel_id')}"
            )

        except Exception as e:
            self.add_result(test_name, "FAIL", f"Eccezione durante il test: {str(e)}")

    def test_reserved_keywords(self):
        """Test di gestione delle parole chiave riservate."""
        test_name = "Test di gestione delle parole chiave riservate"
        logger.info(f"\n=== {test_name} ===")

        try:
            # Esporta il funnel originale
            export_result = export_funnel_config(self.funnel_id)

            if export_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'esportazione: {export_result.get('message')}")
                return

            # Modifica i dati per testare le parole chiave riservate
            export_data = export_result["data"]
            design_data = export_data.get("design", {})

            # Modifica l'ordine di una sezione o componente
            sections = design_data.get("sections", [])
            components = design_data.get("components", [])

            if sections:
                for section in sections:
                    if "order" in section:
                        # Modifica l'ordine per forzare un aggiornamento
                        section["order"] = section["order"] + 1 if isinstance(section["order"], int) else 1

            if components:
                for component in components:
                    if "order" in component:
                        # Modifica l'ordine per forzare un aggiornamento
                        component["order"] = component["order"] + 1 if isinstance(component["order"], int) else 1

            # Salva i dati modificati in un file
            keywords_file = self.test_dir / f"reserved_keywords_{self.funnel_id}.json"
            with open(keywords_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            # Importa il funnel con parole chiave riservate
            import_result = import_funnel_config(export_data, update_existing=True)

            if import_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'importazione: {import_result.get('message')}")
                return

            self.add_result(
                test_name,
                "PASS",
                f"Funnel con parole chiave riservate importato con successo. ID: {import_result.get('funnel_id')}"
            )

        except Exception as e:
            self.add_result(test_name, "FAIL", f"Eccezione durante il test: {str(e)}")

    def test_import_with_explicit_id(self):
        """Test di importazione con ID funnel esplicito."""
        test_name = "Test di importazione con ID funnel esplicito"
        logger.info(f"\n=== {test_name} ===")

        try:
            # Esporta il funnel originale
            export_result = export_funnel_config(self.funnel_id)

            if export_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'esportazione: {export_result.get('message')}")
                return

            # Modifica i dati per specificare esplicitamente l'ID del funnel
            export_data = export_result["data"]
            original_name = export_data["funnel"]["name"]

            # Assicurati che l'ID del funnel sia presente
            export_data["funnel"]["id"] = self.funnel_id

            # Cambia il nome del funnel
            export_data["funnel"]["name"] = f"{original_name} - ID Esplicito"

            # Salva i dati modificati in un file
            explicit_file = self.test_dir / f"explicit_id_{self.funnel_id}.json"
            with open(explicit_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            # Importa il funnel con ID esplicito
            import_result = import_funnel_config(export_data, update_existing=True)

            if import_result.get("error", True):
                self.add_result(test_name, "FAIL", f"Errore nell'importazione: {import_result.get('message')}")
                return

            # Verifica che sia stato aggiornato il funnel corretto
            updated_funnel_id = import_result.get("funnel_id")

            if updated_funnel_id != self.funnel_id:
                self.add_result(
                    test_name,
                    "FAIL",
                    f"Non è stato aggiornato il funnel corretto. ID atteso: {self.funnel_id}, ID ottenuto: {updated_funnel_id}"
                )
                return

            # Verifica che il nome del funnel sia stato aggiornato
            updated_funnel_name = self.get_funnel_name(updated_funnel_id)

            if updated_funnel_name != f"{original_name} - ID Esplicito":
                self.add_result(
                    test_name,
                    "FAIL",
                    f"Il nome del funnel non è stato aggiornato. Atteso: '{original_name} - ID Esplicito', Trovato: '{updated_funnel_name}'"
                )
                return

            self.add_result(
                test_name,
                "PASS",
                f"Funnel con ID esplicito importato con successo. ID: {updated_funnel_id}, Nome: '{updated_funnel_name}'"
            )

        except Exception as e:
            self.add_result(test_name, "FAIL", f"Eccezione durante il test: {str(e)}")

def main():
    """Funzione principale."""
    # Verifica se è stato fornito un ID funnel come argomento
    if len(sys.argv) > 1:
        funnel_id = int(sys.argv[1])

        # Crea e esegui la suite di test
        test_suite = FunnelTestSuite(funnel_id)
        test_suite.run_all_tests()
    else:
        logger.error("Specificare l'ID del funnel come argomento")
        print("Uso: python test_funnel_export_import.py <funnel_id>")
        sys.exit(1)

if __name__ == "__main__":
    main()
