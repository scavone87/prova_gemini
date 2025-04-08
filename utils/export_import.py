"""
Modulo per l'esportazione e l'importazione di configurazioni funnel in formato JSON.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from sqlalchemy import select, text

from db.models import Funnel, Product, Route, Step, Workflow
from utils.db_utils import close_db_session, get_db_session, optimize_query_execution
from utils.error_handler import handle_error, log_operation

# Configurazione del logging
logger = logging.getLogger(__name__)


def export_funnel_config(funnel_id: int) -> Dict[str, Any]:
    """
    Esporta la configurazione di un funnel in un formato JSON completo,
    includendo tutti i dati di design.

    Args:
        funnel_id (int): ID del funnel da esportare

    Returns:
        Dict[str, Any]: Dizionario contenente la configurazione completa del funnel
            o un messaggio di errore in caso di problemi
    """
    session = get_db_session()
    try:
        # Recupera i dati del funnel
        funnel_query = text(
            """
            SELECT f.id, f.name, f.broker_id, f.workflow_id, f.product_id,
                   w.description as workflow_description,
                   p.product_code, p.title_prod
            FROM funnel_manager.funnel f
            JOIN funnel_manager.workflow w ON f.workflow_id = w.id
            JOIN product.products p ON f.product_id = p.id
            WHERE f.id = :funnel_id
        """
        )

        # Prima applico i parametri alla query, poi la eseguo
        funnel_query = funnel_query.bindparams(funnel_id=funnel_id)

        funnel_data = optimize_query_execution(
            session, funnel_query, f"recupero funnel {funnel_id} per export"
        ).fetchone()

        if not funnel_data:
            return {"error": True, "message": f"Funnel con ID {funnel_id} non trovato"}

        workflow_id = funnel_data.workflow_id
        product_id = funnel_data.product_id

        # Recupera gli step del funnel
        steps_query = text(
            """
            SELECT DISTINCT ON (s.id)
                s.id, s.step_url, s.step_code, s.post_message,
                s.shopping_cart, s.gtm_reference
            FROM funnel_manager.step s
            JOIN funnel_manager.route r ON s.id = r.nextstep_id OR s.id = r.fromstep_id
            WHERE r.workflow_id = :workflow_id
            ORDER BY s.id
        """
        )

        # Prima applico i parametri alla query, poi la eseguo
        steps_query = steps_query.bindparams(workflow_id=workflow_id)

        steps = optimize_query_execution(
            session, steps_query, f"step per export del funnel {funnel_id}"
        ).fetchall()

        # Recupera le route del funnel
        routes_query = text(
            """
            SELECT
                r.id, r.fromstep_id, r.nextstep_id, r.route_config,
                fs.step_url as from_step_url,
                ns.step_url as to_step_url
            FROM funnel_manager.route r
            LEFT JOIN funnel_manager.step fs ON r.fromstep_id = fs.id
            LEFT JOIN funnel_manager.step ns ON r.nextstep_id = ns.id
            WHERE r.workflow_id = :workflow_id
        """
        )

        # Prima applico i parametri alla query, poi la eseguo
        routes_query = routes_query.bindparams(workflow_id=workflow_id)

        routes = optimize_query_execution(
            session, routes_query, f"route per export del funnel {funnel_id}"
        ).fetchall()

        # Recupera i dati di design
        # 1. Recupera tutte le sezioni
        sections_query = text(
            """
            SELECT DISTINCT ON (sec.id, ss.id, ss.stepid, ss.productid)
                sec.id, sec.sectiontype,
                ss.id as step_section_id, ss.order, ss.stepid, ss.productid
            FROM design.section sec
            JOIN design.step_section ss ON sec.id = ss.sectionid
            JOIN funnel_manager.step s ON ss.stepid = s.id
            JOIN funnel_manager.route r ON s.id = r.nextstep_id OR s.id = r.fromstep_id
            WHERE r.workflow_id = :workflow_id
            AND (ss.productid IS NULL OR ss.productid = :product_id)
            ORDER BY sec.id, ss.id, ss.stepid, ss.productid
        """
        )

        sections_query = sections_query.bindparams(workflow_id=workflow_id, product_id=product_id)

        sections = optimize_query_execution(
            session, sections_query, f"sezioni per export del funnel {funnel_id}"
        ).fetchall()

        # 2. Recupera tutti i componenti
        components_query = text(
            """
            SELECT DISTINCT ON (c.id, cs.id, cs.sectionid)
                c.id, c.component_type,
                cs.id as component_section_id, cs.order, cs.sectionid
            FROM design.component c
            JOIN design.component_section cs ON c.id = cs.componentid
            JOIN design.section sec ON cs.sectionid = sec.id
            JOIN design.step_section ss ON sec.id = ss.sectionid
            JOIN funnel_manager.step s ON ss.stepid = s.id
            JOIN funnel_manager.route r ON s.id = r.nextstep_id OR s.id = r.fromstep_id
            WHERE r.workflow_id = :workflow_id
            AND (ss.productid IS NULL OR ss.productid = :product_id)
            ORDER BY c.id, cs.id, cs.sectionid
        """
        )

        components_query = components_query.bindparams(workflow_id=workflow_id, product_id=product_id)

        components = optimize_query_execution(
            session, components_query, f"componenti per export del funnel {funnel_id}"
        ).fetchall()

        # 3. Recupera tutte le strutture
        structures_query = text(
            """
            SELECT DISTINCT ON (str.id, scs.id, scs.component_sectionid, scs.order)
                str.id, str.data,
                scs.id as structure_component_section_id, scs.component_sectionid, scs.order
            FROM design.structure str
            JOIN design.structure_component_section scs ON str.id = scs.structureid
            JOIN design.component_section cs ON scs.component_sectionid = cs.id
            JOIN design.section sec ON cs.sectionid = sec.id
            JOIN design.step_section ss ON sec.id = ss.sectionid
            JOIN funnel_manager.step s ON ss.stepid = s.id
            JOIN funnel_manager.route r ON s.id = r.nextstep_id OR s.id = r.fromstep_id
            WHERE r.workflow_id = :workflow_id
            AND (ss.productid IS NULL OR ss.productid = :product_id)
            ORDER BY str.id, scs.id, scs.component_sectionid, scs.order
        """
        )

        structures_query = structures_query.bindparams(workflow_id=workflow_id, product_id=product_id)

        structures = optimize_query_execution(
            session, structures_query, f"strutture per export del funnel {funnel_id}"
        ).fetchall()

        # 4. Recupera tutte le chiavi CMS
        cms_keys_query = text(
            """
            SELECT DISTINCT ON (cms.id, cms.structurecomponentsectionid)
                cms.id, cms.value, cms.structurecomponentsectionid
            FROM design.cms_key cms
            JOIN design.structure_component_section scs ON cms.structurecomponentsectionid = scs.id
            JOIN design.component_section cs ON scs.component_sectionid = cs.id
            JOIN design.section sec ON cs.sectionid = sec.id
            JOIN design.step_section ss ON sec.id = ss.sectionid
            JOIN funnel_manager.step s ON ss.stepid = s.id
            JOIN funnel_manager.route r ON s.id = r.nextstep_id OR s.id = r.fromstep_id
            WHERE r.workflow_id = :workflow_id
            AND (ss.productid IS NULL OR ss.productid = :product_id)
            ORDER BY cms.id, cms.structurecomponentsectionid
        """
        )

        cms_keys_query = cms_keys_query.bindparams(workflow_id=workflow_id, product_id=product_id)

        cms_keys = optimize_query_execution(
            session, cms_keys_query, f"chiavi CMS per export del funnel {funnel_id}"
        ).fetchall()

        # Formatta i risultati
        steps_data = []
        for step in steps:
            # Converti l'oggetto Row in dizionario in modo sicuro
            if hasattr(step, "_asdict"):
                step_dict = step._asdict()
            else:
                # Fallback per altri tipi di oggetti
                step_dict = (
                    {key: getattr(step, key) for key in step.keys()}
                    if hasattr(step, "keys")
                    else {}
                )

            # Converti campi JSON
            for field in ["shopping_cart", "gtm_reference"]:
                if step_dict.get(field) and isinstance(step_dict[field], str):
                    try:
                        step_dict[field] = json.loads(step_dict[field])
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Campo JSON {field} non valido nello step {step_dict.get('id')}"
                        )
                        step_dict[field] = None

            steps_data.append(step_dict)

        routes_data = []
        for route in routes:
            # Converti l'oggetto Row in dizionario in modo sicuro
            if hasattr(route, "_asdict"):
                route_dict = route._asdict()
            else:
                # Fallback per altri tipi di oggetti
                route_dict = (
                    {key: getattr(route, key) for key in route.keys()}
                    if hasattr(route, "keys")
                    else {}
                )

            # Converti campi JSON
            if route_dict.get("route_config") and isinstance(
                route_dict["route_config"], str
            ):
                try:
                    route_dict["route_config"] = json.loads(route_dict["route_config"])
                except json.JSONDecodeError:
                    logger.warning(
                        f"Campo JSON route_config non valido nella route {route_dict.get('id')}"
                    )
                    route_dict["route_config"] = None

            routes_data.append(route_dict)

        # Formatta i dati di design
        sections_data = []
        for section in sections:
            if hasattr(section, "_asdict"):
                section_dict = section._asdict()
            else:
                section_dict = (
                    {key: getattr(section, key) for key in section.keys()}
                    if hasattr(section, "keys")
                    else {}
                )
            sections_data.append(section_dict)

        components_data = []
        for component in components:
            if hasattr(component, "_asdict"):
                component_dict = component._asdict()
            else:
                component_dict = (
                    {key: getattr(component, key) for key in component.keys()}
                    if hasattr(component, "keys")
                    else {}
                )
            components_data.append(component_dict)

        structures_data = []
        for structure in structures:
            if hasattr(structure, "_asdict"):
                structure_dict = structure._asdict()
            else:
                structure_dict = (
                    {key: getattr(structure, key) for key in structure.keys()}
                    if hasattr(structure, "keys")
                    else {}
                )

            # Converti il campo data JSON
            if structure_dict.get("data") and isinstance(structure_dict["data"], str):
                try:
                    structure_dict["data"] = json.loads(structure_dict["data"])
                except json.JSONDecodeError:
                    logger.warning(
                        f"Campo JSON data non valido nella struttura {structure_dict.get('id')}"
                    )
                    structure_dict["data"] = {}

            structures_data.append(structure_dict)

        cms_keys_data = []
        for cms_key in cms_keys:
            if hasattr(cms_key, "_asdict"):
                cms_key_dict = cms_key._asdict()
            else:
                cms_key_dict = (
                    {key: getattr(cms_key, key) for key in cms_key.keys()}
                    if hasattr(cms_key, "keys")
                    else {}
                )

            # Converti il campo value JSON
            if cms_key_dict.get("value") and isinstance(cms_key_dict["value"], str):
                try:
                    cms_key_dict["value"] = json.loads(cms_key_dict["value"])
                except json.JSONDecodeError:
                    logger.warning(
                        f"Campo JSON value non valido nella chiave CMS {cms_key_dict.get('id')}"
                    )
                    cms_key_dict["value"] = {}

            cms_keys_data.append(cms_key_dict)

        # Crea la struttura completa della configurazione
        export_data = {
            "funnel": {
                "id": funnel_data.id,
                "name": funnel_data.name,
                "broker_id": funnel_data.broker_id,
                "product": {
                    "id": funnel_data.product_id,
                    "code": funnel_data.product_code,
                    "name": funnel_data.title_prod,
                },
            },
            "workflow": {
                "id": funnel_data.workflow_id,
                "description": funnel_data.workflow_description,
            },
            "steps": steps_data,
            "routes": routes_data,
            "design": {
                "sections": sections_data,
                "components": components_data,
                "structures": structures_data,
                "cms_keys": cms_keys_data,
            },
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "version": "1.1",
                "includes_design": True
            },
        }

        log_operation("Esportazione funnel completa", {"funnel_id": funnel_id})

        return {"error": False, "data": export_data}
    except Exception as e:
        logger.error(f"Errore nell'esportazione del funnel {funnel_id}: {e}")
        return handle_error(
            e,
            f"Errore nell'esportazione del funnel {funnel_id}",
            fallback_data={"error": True, "message": str(e)},
        )
    finally:
        close_db_session(session)


def import_funnel_config(
    config_data: Dict[str, Any], update_existing: bool = False
) -> Dict[str, Any]:
    """
    Importa una configurazione funnel da un dizionario JSON.
    Supporta l'importazione completa, inclusi i dati di design.

    Args:
        config_data (Dict[str, Any]): Dati di configurazione da importare
        update_existing (bool): Se True, aggiorna un funnel esistente se trovato,
                               altrimenti crea un nuovo funnel

    Returns:
        Dict[str, Any]: Dizionario con i risultati dell'importazione
    """
    session = get_db_session()
    try:
        # Validazione iniziale della struttura
        required_fields = ["funnel", "workflow", "steps", "routes"]
        for field in required_fields:
            if field not in config_data:
                return {
                    "error": True,
                    "message": f"Campo {field} mancante nella configurazione",
                }

        # Verifica se ci sono dati di design
        has_design_data = "design" in config_data and isinstance(config_data["design"], dict)

        # Inizio transazione
        session.begin()

        # Otteniamo i dati dal file di configurazione
        funnel_data = config_data["funnel"]
        workflow_data = config_data["workflow"]
        steps_data = config_data["steps"]
        routes_data = config_data["routes"]

        # Estrai i dati di design se presenti
        design_data = config_data.get("design", {})
        sections_data = design_data.get("sections", [])
        components_data = design_data.get("components", [])
        structures_data = design_data.get("structures", [])
        cms_keys_data = design_data.get("cms_keys", [])

        # Verifica se il funnel esiste già
        product_id = funnel_data["product"]["id"]
        funnel_id_from_import = funnel_data.get("id")

        # Se abbiamo l'ID del funnel nel file di importazione, cerchiamo prima per ID
        if funnel_id_from_import:
            existing_funnel_by_id_query = text(
                """
                SELECT f.id, f.name, f.workflow_id
                FROM funnel_manager.funnel f
                WHERE f.id = :funnel_id
            """
            ).bindparams(funnel_id=funnel_id_from_import)

            existing_funnel = session.execute(existing_funnel_by_id_query).fetchone()

            if existing_funnel:
                logger.info(f"Trovato funnel esistente con ID {funnel_id_from_import}")

        # Se non abbiamo trovato il funnel per ID, cerchiamo per product_id
        if not funnel_id_from_import or not existing_funnel:
            existing_funnel_query = text(
                """
                SELECT f.id, f.name, f.workflow_id
                FROM funnel_manager.funnel f
                WHERE f.product_id = :product_id
            """
            ).bindparams(product_id=product_id)

            existing_funnels = session.execute(existing_funnel_query).fetchall()

            if len(existing_funnels) > 1:
                logger.warning(f"Trovati {len(existing_funnels)} funnel per il prodotto {product_id}. Verrà aggiornato il primo.")
                existing_funnel = existing_funnels[0]
            elif len(existing_funnels) == 1:
                existing_funnel = existing_funnels[0]
                logger.info(f"Trovato funnel esistente con ID {existing_funnel.id} per il prodotto {product_id}")
            else:
                existing_funnel = None

        # Se il funnel esiste già e non vogliamo aggiornarlo, restituisci un errore
        if existing_funnel and not update_existing:
            funnel_name = existing_funnel.name if hasattr(existing_funnel, 'name') else 'sconosciuto'
            return {
                "error": True,
                "message": f"Esiste già un funnel '{funnel_name}' (ID: {existing_funnel.id}) per il prodotto {product_id}. Usa l'opzione 'update_existing' per aggiornarlo.",
            }

        # Variabili per tenere traccia degli ID
        workflow_id = None
        funnel_id = None
        original_to_new_step_ids = {}  # Mappatura tra gli ID di step del file e gli ID nel database

        # Gestisci il workflow - crea o aggiorna
        if existing_funnel and update_existing:
            # Se aggiorniamo un funnel esistente, ottieni l'ID del workflow esistente
            workflow_id = existing_funnel.workflow_id
            funnel_id = existing_funnel.id

            # Aggiorna la descrizione del workflow
            workflow_update_query = text(
                """
                UPDATE funnel_manager.workflow
                SET description = :description
                WHERE id = :workflow_id
                RETURNING id
            """
            ).bindparams(
                description=workflow_data["description"], workflow_id=workflow_id
            )

            session.execute(workflow_update_query)

            # Aggiorna il funnel
            funnel_update_query = text(
                """
                UPDATE funnel_manager.funnel
                SET name = :name, broker_id = :broker_id
                WHERE id = :funnel_id
                RETURNING id
            """
            ).bindparams(
                name=funnel_data["name"],
                broker_id=funnel_data["broker_id"],
                funnel_id=funnel_id,
            )

            session.execute(funnel_update_query)

            # Elimina step e route esistenti per ricrearli puliti
            # Questo approccio semplifica la gestione delle relazioni
            session.execute(
                text(
                    """
                DELETE FROM funnel_manager.route
                WHERE workflow_id = :workflow_id
            """
                ).bindparams(workflow_id=workflow_id)
            )

            # Ottieni gli step esistenti per il workflow
            existing_steps = session.execute(
                text(
                    """
                SELECT DISTINCT s.id, s.step_url
                FROM funnel_manager.step s
                JOIN funnel_manager.route r ON s.id = r.nextstep_id OR s.id = r.fromstep_id
                WHERE r.workflow_id = :workflow_id
            """
                ).bindparams(workflow_id=workflow_id)
            ).fetchall()

            # Crea una mappatura degli step esistenti per URL
            existing_steps_by_url = {step.step_url: step.id for step in existing_steps}

        else:
            # Crea un nuovo workflow
            workflow_query = text(
                """
                INSERT INTO funnel_manager.workflow (description)
                VALUES (:description)
                RETURNING id
            """
            ).bindparams(description=workflow_data["description"])

            workflow_id = session.execute(workflow_query).fetchone()[0]

            # Crea un nuovo funnel
            funnel_query = text(
                """
                INSERT INTO funnel_manager.funnel (name, broker_id, product_id, workflow_id)
                VALUES (:name, :broker_id, :product_id, :workflow_id)
                RETURNING id
            """
            ).bindparams(
                name=funnel_data["name"],
                broker_id=funnel_data["broker_id"],
                product_id=product_id,
                workflow_id=workflow_id,
            )

            funnel_id = session.execute(funnel_query).fetchone()[0]
            existing_steps_by_url = {}

        # Importazione degli step
        imported_step_ids = []
        original_to_new_step_ids = {}  # Mappatura tra ID originali e nuovi

        for step in steps_data:
            # Prepare JSON fields
            shopping_cart = (
                json.dumps(step["shopping_cart"]) if step["shopping_cart"] else None
            )
            gtm_reference = (
                json.dumps(step["gtm_reference"]) if step["gtm_reference"] else None
            )

            # Verifica se esiste già uno step con questo URL
            step_url = step["step_url"]

            # Verifica se lo step esiste già nel mapping locale
            if step_url in existing_steps_by_url and update_existing:
                step_id = existing_steps_by_url[step_url]

                # Aggiorna lo step esistente
                step_update_query = text(
                    """
                    UPDATE funnel_manager.step
                    SET step_code = :step_code,
                        post_message = :post_message,
                        shopping_cart = :shopping_cart,
                        gtm_reference = :gtm_reference
                    WHERE id = :step_id
                    RETURNING id
                """
                ).bindparams(
                    step_code=step["step_code"],
                    post_message=step["post_message"],
                    shopping_cart=shopping_cart,
                    gtm_reference=gtm_reference,
                    step_id=step_id,
                )

                step_id = session.execute(step_update_query).fetchone()[0]
            else:
                # Verifica se esiste già uno step con questo URL nel database
                existing_step_query = text(
                    """
                    SELECT id FROM funnel_manager.step
                    WHERE step_url = :step_url
                """
                ).bindparams(step_url=step_url)

                existing_step = session.execute(existing_step_query).fetchone()

                if existing_step:
                    # Usa lo step esistente e aggiornalo
                    step_id = existing_step[0]

                    # Aggiorna lo step esistente
                    step_update_query = text(
                        """
                        UPDATE funnel_manager.step
                        SET step_code = :step_code,
                            post_message = :post_message,
                            shopping_cart = :shopping_cart,
                            gtm_reference = :gtm_reference
                        WHERE id = :step_id
                        RETURNING id
                    """
                    ).bindparams(
                        step_code=step["step_code"],
                        post_message=step["post_message"],
                        shopping_cart=shopping_cart,
                        gtm_reference=gtm_reference,
                        step_id=step_id,
                    )

                    step_id = session.execute(step_update_query).fetchone()[0]

                    # Aggiungi lo step al mapping locale per futuri riferimenti
                    existing_steps_by_url[step_url] = step_id
                else:
                    # Crea un nuovo step
                    step_insert_query = text(
                        """
                        INSERT INTO funnel_manager.step (
                            step_url, step_code, post_message,
                            shopping_cart, gtm_reference
                        )
                        VALUES (
                            :step_url, :step_code, :post_message,
                            :shopping_cart, :gtm_reference
                        )
                        RETURNING id
                    """
                    ).bindparams(
                        step_url=step["step_url"],
                        step_code=step["step_code"],
                        post_message=step["post_message"],
                        shopping_cart=shopping_cart,
                        gtm_reference=gtm_reference,
                    )

                    try:
                        step_id = session.execute(step_insert_query).fetchone()[0]
                        # Aggiungi lo step al mapping locale per futuri riferimenti
                        existing_steps_by_url[step_url] = step_id
                    except Exception as e:
                        # Se l'inserimento fallisce (ad esempio per una race condition),
                        # riprova a cercare lo step esistente
                        logger.warning(f"Errore nell'inserimento dello step {step_url}: {e}")
                        existing_step = session.execute(existing_step_query).fetchone()
                        if existing_step:
                            step_id = existing_step[0]
                            existing_steps_by_url[step_url] = step_id
                        else:
                            # Se ancora non troviamo lo step, solleva l'eccezione
                            raise

            # Aggiorna la mappatura
            imported_step_ids.append(step_id)
            original_to_new_step_ids[step["id"]] = step_id

        # Importazione delle route
        imported_route_ids = []

        for route in routes_data:
            # Verifica che gli step esistano nella mappatura
            from_step_id = original_to_new_step_ids.get(route["fromstep_id"])
            next_step_id = original_to_new_step_ids.get(route["nextstep_id"])

            if not from_step_id or not next_step_id:
                logger.warning(
                    f"Skip route con step mancanti: fromstep_id={route['fromstep_id']}, nextstep_id={route['nextstep_id']}"
                )
                continue

            # Prepare JSON fields
            route_config = (
                json.dumps(route["route_config"]) if route["route_config"] else None
            )

            # Crea la route
            route_insert_query = text(
                """
                INSERT INTO funnel_manager.route (
                    workflow_id, fromstep_id, nextstep_id, route_config
                )
                VALUES (
                    :workflow_id, :fromstep_id, :nextstep_id, :route_config
                )
                RETURNING id
            """
            ).bindparams(
                workflow_id=workflow_id,
                fromstep_id=from_step_id,
                nextstep_id=next_step_id,
                route_config=route_config,
            )

            route_id = session.execute(route_insert_query).fetchone()[0]
            imported_route_ids.append(route_id)

        # Importazione dei dati di design se presenti
        imported_design_elements = {
            "sections": 0,
            "components": 0,
            "structures": 0,
            "cms_keys": 0
        }

        if has_design_data:
            # Mappatura per tenere traccia degli ID originali e nuovi
            section_mapping = {}  # ID originale -> ID nuovo
            component_mapping = {}
            component_section_mapping = {}
            structure_mapping = {}
            structure_component_section_mapping = {}

            # Se stiamo aggiornando un funnel esistente, eliminiamo prima i dati di design esistenti
            if update_existing:
                # Ottieni gli step IDs per questo workflow
                step_ids_query = text("""
                    SELECT DISTINCT s.id
                    FROM funnel_manager.step s
                    JOIN funnel_manager.route r ON s.id = r.nextstep_id OR s.id = r.fromstep_id
                    WHERE r.workflow_id = :workflow_id
                """).bindparams(workflow_id=workflow_id)

                step_ids = [row[0] for row in session.execute(step_ids_query).fetchall()]

                if step_ids:
                    # Elimina le relazioni step_section per questi step
                    step_ids_str = ", ".join([str(id) for id in step_ids])

                    # Ottieni gli ID delle sezioni associate a questi step
                    section_ids_query = text(f"""
                        SELECT DISTINCT ss.sectionid
                        FROM design.step_section ss
                        WHERE ss.stepid IN ({step_ids_str})
                        AND (ss.productid IS NULL OR ss.productid = :product_id)
                    """).bindparams(product_id=product_id)

                    section_ids = [row[0] for row in session.execute(section_ids_query).fetchall()]

                    if section_ids:
                        # Elimina le relazioni step_section
                        session.execute(text(f"""
                            DELETE FROM design.step_section
                            WHERE stepid IN ({step_ids_str})
                            AND (productid IS NULL OR productid = :product_id)
                        """).bindparams(product_id=product_id))

                        # Ottieni gli ID delle component_section associate a queste sezioni
                        section_ids_str = ", ".join([str(id) for id in section_ids])
                        component_section_ids_query = text(f"""
                            SELECT DISTINCT id
                            FROM design.component_section
                            WHERE sectionid IN ({section_ids_str})
                        """)

                        component_section_ids = [row[0] for row in session.execute(component_section_ids_query).fetchall()]

                        if component_section_ids:
                            # Ottieni gli ID delle structure_component_section associate
                            component_section_ids_str = ", ".join([str(id) for id in component_section_ids])
                            structure_component_section_ids_query = text(f"""
                                SELECT DISTINCT id
                                FROM design.structure_component_section
                                WHERE component_sectionid IN ({component_section_ids_str})
                            """)

                            structure_component_section_ids = [row[0] for row in session.execute(structure_component_section_ids_query).fetchall()]

                            if structure_component_section_ids:
                                # Elimina le chiavi CMS associate
                                structure_component_section_ids_str = ", ".join([str(id) for id in structure_component_section_ids])
                                session.execute(text(f"""
                                    DELETE FROM design.cms_key
                                    WHERE structurecomponentsectionid IN ({structure_component_section_ids_str})
                                """))

                                # Elimina le structure_component_section
                                session.execute(text(f"""
                                    DELETE FROM design.structure_component_section
                                    WHERE id IN ({structure_component_section_ids_str})
                                """))

                            # Elimina le component_section
                            session.execute(text(f"""
                                DELETE FROM design.component_section
                                WHERE id IN ({component_section_ids_str})
                            """))

            # Importa le sezioni
            for section in sections_data:
                original_id = section["id"]
                section_type = section["sectiontype"]

                # Verifica se la sezione esiste già (solo per sicurezza)
                section_check_query = text("""
                    SELECT id FROM design.section WHERE id = :id
                """).bindparams(id=original_id)

                existing_section = session.execute(section_check_query).fetchone()

                if existing_section:
                    # Aggiorna la sezione esistente
                    section_update_query = text("""
                        UPDATE design.section
                        SET sectiontype = :sectiontype
                        WHERE id = :id
                        RETURNING id
                    """).bindparams(id=original_id, sectiontype=section_type)

                    section_id = session.execute(section_update_query).fetchone()[0]
                else:
                    # Crea una nuova sezione
                    section_insert_query = text("""
                        INSERT INTO design.section (id, sectiontype)
                        VALUES (:id, :sectiontype)
                        ON CONFLICT (id) DO UPDATE SET sectiontype = :sectiontype
                        RETURNING id
                    """).bindparams(id=original_id, sectiontype=section_type)

                    section_id = session.execute(section_insert_query).fetchone()[0]

                section_mapping[original_id] = section_id
                imported_design_elements["sections"] += 1

                # Crea la relazione step_section se presente
                if "stepid" in section and "step_section_id" in section:
                    step_id = original_to_new_step_ids.get(section["stepid"])
                    if step_id:
                        step_section_insert_query = text("""
                            INSERT INTO design.step_section (
                                id, "order", sectionid, stepid, productid
                            )
                            VALUES (
                                :id, :order, :sectionid, :stepid, :productid
                            )
                            ON CONFLICT (id) DO UPDATE SET
                                "order" = :order,
                                sectionid = :sectionid,
                                stepid = :stepid,
                                productid = :productid
                            RETURNING id
                        """).bindparams(
                            id=section["step_section_id"],
                            order=section.get("order", 0),
                            sectionid=section_id,
                            stepid=step_id,
                            productid=section.get("productid")
                        )

                        session.execute(step_section_insert_query)

            # Importa i componenti
            for component in components_data:
                original_id = component["id"]
                component_type = component["component_type"]

                # Verifica se il componente esiste già
                component_check_query = text("""
                    SELECT id FROM design.component WHERE id = :id
                """).bindparams(id=original_id)

                existing_component = session.execute(component_check_query).fetchone()

                if existing_component:
                    # Aggiorna il componente esistente
                    component_update_query = text("""
                        UPDATE design.component
                        SET component_type = :component_type
                        WHERE id = :id
                        RETURNING id
                    """).bindparams(id=original_id, component_type=component_type)

                    component_id = session.execute(component_update_query).fetchone()[0]
                else:
                    # Crea un nuovo componente
                    component_insert_query = text("""
                        INSERT INTO design.component (id, component_type)
                        VALUES (:id, :component_type)
                        ON CONFLICT (id) DO UPDATE SET component_type = :component_type
                        RETURNING id
                    """).bindparams(id=original_id, component_type=component_type)

                    component_id = session.execute(component_insert_query).fetchone()[0]

                component_mapping[original_id] = component_id
                imported_design_elements["components"] += 1

                # Crea la relazione component_section se presente
                if "sectionid" in component and "component_section_id" in component:
                    section_id = section_mapping.get(component["sectionid"])
                    if section_id:
                        component_section_insert_query = text("""
                            INSERT INTO design.component_section (
                                id, componentid, sectionid, "order"
                            )
                            VALUES (
                                :id, :componentid, :sectionid, :order
                            )
                            ON CONFLICT (id) DO UPDATE SET
                                componentid = :componentid,
                                sectionid = :sectionid,
                                "order" = :order
                            RETURNING id
                        """).bindparams(
                            id=component["component_section_id"],
                            componentid=component_id,
                            sectionid=section_id,
                            order=component.get("order", 0)
                        )

                        component_section_id = session.execute(component_section_insert_query).fetchone()[0]
                        component_section_mapping[component["component_section_id"]] = component_section_id

            # Importa le strutture
            for structure in structures_data:
                original_id = structure["id"]
                # Assicurati che il valore sia serializzato in JSON se è un dizionario o una lista
                if isinstance(structure["data"], (dict, list)):
                    structure_data = json.dumps(structure["data"])
                else:
                    structure_data = structure["data"]

                # Verifica se la struttura esiste già
                structure_check_query = text("""
                    SELECT id FROM design.structure WHERE id = :id
                """).bindparams(id=original_id)

                existing_structure = session.execute(structure_check_query).fetchone()

                if existing_structure:
                    # Aggiorna la struttura esistente
                    structure_update_query = text("""
                        UPDATE design.structure
                        SET data = :data
                        WHERE id = :id
                        RETURNING id
                    """).bindparams(id=original_id, data=structure_data)

                    structure_id = session.execute(structure_update_query).fetchone()[0]
                else:
                    # Crea una nuova struttura
                    structure_insert_query = text("""
                        INSERT INTO design.structure (id, data)
                        VALUES (:id, :data)
                        ON CONFLICT (id) DO UPDATE SET data = :data
                        RETURNING id
                    """).bindparams(id=original_id, data=structure_data)

                    structure_id = session.execute(structure_insert_query).fetchone()[0]

                structure_mapping[original_id] = structure_id
                imported_design_elements["structures"] += 1

                # Crea la relazione structure_component_section se presente
                if "component_sectionid" in structure and "structure_component_section_id" in structure:
                    component_section_id = component_section_mapping.get(structure["component_sectionid"])
                    if component_section_id:
                        structure_component_section_insert_query = text("""
                            INSERT INTO design.structure_component_section (
                                id, component_sectionid, structureid, "order"
                            )
                            VALUES (
                                :id, :component_sectionid, :structureid, :order
                            )
                            ON CONFLICT (id) DO UPDATE SET
                                component_sectionid = :component_sectionid,
                                structureid = :structureid,
                                "order" = :order
                            RETURNING id
                        """).bindparams(
                            id=structure["structure_component_section_id"],
                            component_sectionid=component_section_id,
                            structureid=structure_id,
                            order=structure.get("order", 0)
                        )

                        structure_component_section_id = session.execute(structure_component_section_insert_query).fetchone()[0]
                        structure_component_section_mapping[structure["structure_component_section_id"]] = structure_component_section_id

            # Importa le chiavi CMS
            for cms_key in cms_keys_data:
                original_id = cms_key["id"]
                # Assicurati che il valore sia serializzato in JSON se è un dizionario o una lista
                if isinstance(cms_key["value"], (dict, list)):
                    cms_value = json.dumps(cms_key["value"])
                else:
                    cms_value = cms_key["value"]
                structure_component_section_id = structure_component_section_mapping.get(cms_key["structurecomponentsectionid"])

                if structure_component_section_id:
                    # Verifica se la chiave CMS esiste già
                    cms_key_check_query = text("""
                        SELECT id FROM design.cms_key WHERE id = :id
                    """).bindparams(id=original_id)

                    existing_cms_key = session.execute(cms_key_check_query).fetchone()

                    if existing_cms_key:
                        # Aggiorna la chiave CMS esistente
                        cms_key_update_query = text("""
                            UPDATE design.cms_key
                            SET value = :value, structurecomponentsectionid = :structurecomponentsectionid
                            WHERE id = :id
                            RETURNING id
                        """).bindparams(
                            id=original_id,
                            value=cms_value,
                            structurecomponentsectionid=structure_component_section_id
                        )

                        session.execute(cms_key_update_query)
                    else:
                        # Crea una nuova chiave CMS
                        cms_key_insert_query = text("""
                            INSERT INTO design.cms_key (id, value, structurecomponentsectionid)
                            VALUES (:id, :value, :structurecomponentsectionid)
                            ON CONFLICT (id) DO UPDATE SET
                                value = :value,
                                structurecomponentsectionid = :structurecomponentsectionid
                            RETURNING id
                        """).bindparams(
                            id=original_id,
                            value=cms_value,
                            structurecomponentsectionid=structure_component_section_id
                        )

                        session.execute(cms_key_insert_query)

                    imported_design_elements["cms_keys"] += 1

        # Commit della transazione
        session.commit()

        import_result = {
            "error": False,
            "message": (
                "Funnel importato con successo"
                if not (existing_funnel and update_existing)
                else "Funnel aggiornato con successo"
            ),
            "funnel_id": funnel_id,
            "steps_imported": len(imported_step_ids),
            "routes_imported": len(imported_route_ids),
            "design_imported": imported_design_elements if has_design_data else None
        }

        log_operation(
            "Importazione configurazione funnel",
            {
                "funnel_id": funnel_id,
                "product_id": product_id,
                "update_existing": update_existing,
            },
        )

        return import_result
    except Exception as e:
        session.rollback()
        logger.error(f"Errore nell'importazione della configurazione funnel: {e}")
        return handle_error(
            e,
            f"Errore nell'importazione della configurazione funnel",
            fallback_data={"error": True, "message": str(e)},
        )
    finally:
        close_db_session(session)


def format_export_for_download(funnel_config: Dict[str, Any]) -> str:
    """
    Formatta la configurazione del funnel per il download come file JSON.

    Args:
        funnel_config (Dict[str, Any]): Configurazione del funnel

    Returns:
        str: Stringa JSON formattata
    """
    if funnel_config.get("error", False):
        return json.dumps(
            {
                "error": True,
                "message": funnel_config.get("message", "Errore sconosciuto"),
            }
        )

    # Estrai i dati se necessario
    data = funnel_config.get("data", funnel_config)

    # Formatta il JSON con indentazione per leggibilità
    return json.dumps(data, indent=2, ensure_ascii=False)
