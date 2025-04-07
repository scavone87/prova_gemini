"""
Modulo per l'esportazione e l'importazione di configurazioni funnel in formato JSON.
"""

import json
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import select, text
from db.models import Funnel, Workflow, Step, Route, Product
from utils.db_utils import get_db_session, close_db_session, optimize_query_execution
from utils.error_handler import handle_error, log_operation
from typing import Dict, List, Any, Optional, Tuple, Union

# Configurazione del logging
logger = logging.getLogger(__name__)

def export_funnel_config(funnel_id: int) -> Dict[str, Any]:
    """
    Esporta la configurazione di un funnel in un formato JSON completo.
    
    Args:
        funnel_id (int): ID del funnel da esportare
        
    Returns:
        Dict[str, Any]: Dizionario contenente la configurazione completa del funnel
            o un messaggio di errore in caso di problemi
    """
    session = get_db_session()
    try:
        # Recupera i dati del funnel
        funnel_query = text("""
            SELECT f.id, f.name, f.broker_id, f.workflow_id, f.product_id, 
                   w.description as workflow_description,
                   p.product_code, p.title_prod
            FROM funnel_manager.funnel f
            JOIN funnel_manager.workflow w ON f.workflow_id = w.id
            JOIN product.products p ON f.product_id = p.id
            WHERE f.id = :funnel_id
        """)
        
        # Prima applico i parametri alla query, poi la eseguo
        funnel_query = funnel_query.bindparams(funnel_id=funnel_id)
        
        funnel_data = optimize_query_execution(
            session,
            funnel_query,
            f"recupero funnel {funnel_id} per export"
        ).fetchone()
        
        if not funnel_data:
            return {
                'error': True,
                'message': f"Funnel con ID {funnel_id} non trovato"
            }
        
        workflow_id = funnel_data.workflow_id
        
        # Recupera gli step del funnel
        steps_query = text("""
            SELECT DISTINCT 
                s.id, s.step_url, s.step_code, s.post_message,
                s.shopping_cart, s.gtm_reference
            FROM funnel_manager.step s
            JOIN funnel_manager.route r ON s.id = r.nextstep_id OR s.id = r.fromstep_id
            WHERE r.workflow_id = :workflow_id
        """)
        
        # Prima applico i parametri alla query, poi la eseguo
        steps_query = steps_query.bindparams(workflow_id=workflow_id)
        
        steps = optimize_query_execution(
            session,
            steps_query,
            f"step per export del funnel {funnel_id}"
        ).fetchall()
        
        # Recupera le route del funnel
        routes_query = text("""
            SELECT 
                r.id, r.fromstep_id, r.nextstep_id, r.route_config,
                fs.step_url as from_step_url, 
                ns.step_url as to_step_url
            FROM funnel_manager.route r
            LEFT JOIN funnel_manager.step fs ON r.fromstep_id = fs.id
            LEFT JOIN funnel_manager.step ns ON r.nextstep_id = ns.id
            WHERE r.workflow_id = :workflow_id
        """)
        
        # Prima applico i parametri alla query, poi la eseguo
        routes_query = routes_query.bindparams(workflow_id=workflow_id)
        
        routes = optimize_query_execution(
            session,
            routes_query,
            f"route per export del funnel {funnel_id}"
        ).fetchall()
        
        # Formatta i risultati
        steps_data = []
        for step in steps:
            # Converti l'oggetto Row in dizionario in modo sicuro
            if hasattr(step, "_asdict"):
                step_dict = step._asdict()
            else:
                # Fallback per altri tipi di oggetti
                step_dict = {key: getattr(step, key) for key in step.keys()} if hasattr(step, "keys") else {}
            
            # Converti campi JSON
            for field in ['shopping_cart', 'gtm_reference']:
                if step_dict.get(field) and isinstance(step_dict[field], str):
                    try:
                        step_dict[field] = json.loads(step_dict[field])
                    except json.JSONDecodeError:
                        logger.warning(f"Campo JSON {field} non valido nello step {step_dict.get('id')}")
                        step_dict[field] = None
            
            steps_data.append(step_dict)
        
        routes_data = []
        for route in routes:
            # Converti l'oggetto Row in dizionario in modo sicuro
            if hasattr(route, "_asdict"):
                route_dict = route._asdict()
            else:
                # Fallback per altri tipi di oggetti
                route_dict = {key: getattr(route, key) for key in route.keys()} if hasattr(route, "keys") else {}
            
            # Converti campi JSON
            if route_dict.get('route_config') and isinstance(route_dict['route_config'], str):
                try:
                    route_dict['route_config'] = json.loads(route_dict['route_config'])
                except json.JSONDecodeError:
                    logger.warning(f"Campo JSON route_config non valido nella route {route_dict.get('id')}")
                    route_dict['route_config'] = None
            
            routes_data.append(route_dict)
        
        # Crea la struttura completa della configurazione
        export_data = {
            "funnel": {
                "id": funnel_data.id,
                "name": funnel_data.name,
                "broker_id": funnel_data.broker_id,
                "product": {
                    "id": funnel_data.product_id,
                    "code": funnel_data.product_code,
                    "name": funnel_data.title_prod
                }
            },
            "workflow": {
                "id": funnel_data.workflow_id,
                "description": funnel_data.workflow_description
            },
            "steps": steps_data,
            "routes": routes_data,
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        log_operation("Esportazione funnel", {"funnel_id": funnel_id})
        
        return {
            "error": False,
            "data": export_data
        }
    except Exception as e:
        logger.error(f"Errore nell'esportazione del funnel {funnel_id}: {e}")
        return handle_error(
            e,
            f"Errore nell'esportazione del funnel {funnel_id}",
            fallback_data={"error": True, "message": str(e)}
        )
    finally:
        close_db_session(session)

def import_funnel_config(config_data: Dict[str, Any], 
                         update_existing: bool = False) -> Dict[str, Any]:
    """
    Importa una configurazione funnel da un dizionario JSON.
    
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
        required_fields = ['funnel', 'workflow', 'steps', 'routes']
        for field in required_fields:
            if field not in config_data:
                return {
                    'error': True,
                    'message': f"Campo {field} mancante nella configurazione"
                }
        
        # Inizio transazione
        session.begin()
        
        # Otteniamo i dati dal file di configurazione
        funnel_data = config_data['funnel']
        workflow_data = config_data['workflow']
        steps_data = config_data['steps']
        routes_data = config_data['routes']
        
        # Verifica se il funnel esiste già
        product_id = funnel_data['product']['id']
        existing_funnel_query = text("""
            SELECT f.id, f.name, f.workflow_id
            FROM funnel_manager.funnel f
            WHERE f.product_id = :product_id
        """).bindparams(product_id=product_id)
        
        existing_funnel = session.execute(existing_funnel_query).fetchone()
        
        # Variabili per tenere traccia degli ID
        workflow_id = None
        funnel_id = None
        step_mapping = {}  # Mappatura tra gli ID di step del file e gli ID nel database
        
        # Gestisci il workflow - crea o aggiorna
        if existing_funnel and update_existing:
            # Se aggiorniamo un funnel esistente, ottieni l'ID del workflow esistente
            workflow_id = existing_funnel.workflow_id
            funnel_id = existing_funnel.id
            
            # Aggiorna la descrizione del workflow
            workflow_update_query = text("""
                UPDATE funnel_manager.workflow
                SET description = :description
                WHERE id = :workflow_id
                RETURNING id
            """).bindparams(
                description=workflow_data['description'],
                workflow_id=workflow_id
            )
            
            session.execute(workflow_update_query)
            
            # Aggiorna il funnel
            funnel_update_query = text("""
                UPDATE funnel_manager.funnel
                SET name = :name, broker_id = :broker_id
                WHERE id = :funnel_id
                RETURNING id
            """).bindparams(
                name=funnel_data['name'],
                broker_id=funnel_data['broker_id'],
                funnel_id=funnel_id
            )
            
            session.execute(funnel_update_query)
            
            # Elimina step e route esistenti per ricrearli puliti
            # Questo approccio semplifica la gestione delle relazioni
            session.execute(text("""
                DELETE FROM funnel_manager.route
                WHERE workflow_id = :workflow_id
            """).bindparams(workflow_id=workflow_id))
            
            # Ottieni gli step esistenti per il workflow
            existing_steps = session.execute(text("""
                SELECT DISTINCT s.id, s.step_url 
                FROM funnel_manager.step s
                JOIN funnel_manager.route r ON s.id = r.nextstep_id OR s.id = r.fromstep_id
                WHERE r.workflow_id = :workflow_id
            """).bindparams(workflow_id=workflow_id)).fetchall()
            
            # Crea una mappatura degli step esistenti per URL
            existing_steps_by_url = {step.step_url: step.id for step in existing_steps}
            
        else:
            # Crea un nuovo workflow
            workflow_query = text("""
                INSERT INTO funnel_manager.workflow (description)
                VALUES (:description)
                RETURNING id
            """).bindparams(description=workflow_data['description'])
            
            workflow_id = session.execute(workflow_query).fetchone()[0]
            
            # Crea un nuovo funnel
            funnel_query = text("""
                INSERT INTO funnel_manager.funnel (name, broker_id, product_id, workflow_id)
                VALUES (:name, :broker_id, :product_id, :workflow_id)
                RETURNING id
            """).bindparams(
                name=funnel_data['name'],
                broker_id=funnel_data['broker_id'],
                product_id=product_id,
                workflow_id=workflow_id
            )
            
            funnel_id = session.execute(funnel_query).fetchone()[0]
            existing_steps_by_url = {}
        
        # Importazione degli step
        imported_step_ids = []
        original_to_new_step_ids = {}  # Mappatura tra ID originali e nuovi
        
        for step in steps_data:
            # Prepare JSON fields
            shopping_cart = json.dumps(step['shopping_cart']) if step['shopping_cart'] else None
            gtm_reference = json.dumps(step['gtm_reference']) if step['gtm_reference'] else None
            
            # Verifica se esiste già uno step con questo URL
            step_url = step['step_url']
            if step_url in existing_steps_by_url and update_existing:
                step_id = existing_steps_by_url[step_url]
                
                # Aggiorna lo step esistente
                step_update_query = text("""
                    UPDATE funnel_manager.step
                    SET step_code = :step_code,
                        post_message = :post_message,
                        shopping_cart = :shopping_cart,
                        gtm_reference = :gtm_reference
                    WHERE id = :step_id
                    RETURNING id
                """).bindparams(
                    step_code=step['step_code'],
                    post_message=step['post_message'],
                    shopping_cart=shopping_cart,
                    gtm_reference=gtm_reference,
                    step_id=step_id
                )
                
                step_id = session.execute(step_update_query).fetchone()[0]
            else:
                # Crea un nuovo step
                step_insert_query = text("""
                    INSERT INTO funnel_manager.step (
                        step_url, step_code, post_message, 
                        shopping_cart, gtm_reference
                    )
                    VALUES (
                        :step_url, :step_code, :post_message,
                        :shopping_cart, :gtm_reference
                    )
                    RETURNING id
                """).bindparams(
                    step_url=step['step_url'],
                    step_code=step['step_code'],
                    post_message=step['post_message'],
                    shopping_cart=shopping_cart,
                    gtm_reference=gtm_reference
                )
                
                step_id = session.execute(step_insert_query).fetchone()[0]
            
            # Aggiorna la mappatura
            imported_step_ids.append(step_id)
            original_to_new_step_ids[step['id']] = step_id
        
        # Importazione delle route
        imported_route_ids = []
        
        for route in routes_data:
            # Verifica che gli step esistano nella mappatura
            from_step_id = original_to_new_step_ids.get(route['fromstep_id'])
            next_step_id = original_to_new_step_ids.get(route['nextstep_id'])
            
            if not from_step_id or not next_step_id:
                logger.warning(f"Skip route con step mancanti: fromstep_id={route['fromstep_id']}, nextstep_id={route['nextstep_id']}")
                continue
            
            # Prepare JSON fields
            route_config = json.dumps(route['route_config']) if route['route_config'] else None
            
            # Crea la route
            route_insert_query = text("""
                INSERT INTO funnel_manager.route (
                    workflow_id, fromstep_id, nextstep_id, route_config
                )
                VALUES (
                    :workflow_id, :fromstep_id, :nextstep_id, :route_config
                )
                RETURNING id
            """).bindparams(
                workflow_id=workflow_id,
                fromstep_id=from_step_id,
                nextstep_id=next_step_id,
                route_config=route_config
            )
            
            route_id = session.execute(route_insert_query).fetchone()[0]
            imported_route_ids.append(route_id)
        
        # Commit della transazione
        session.commit()
        
        import_result = {
            'error': False,
            'message': "Funnel importato con successo" if not (existing_funnel and update_existing) else 
                     "Funnel aggiornato con successo",
            'funnel_id': funnel_id,
            'steps_imported': len(imported_step_ids),
            'routes_imported': len(imported_route_ids)
        }
        
        log_operation(
            "Importazione configurazione funnel", 
            {"funnel_id": funnel_id, "product_id": product_id, "update_existing": update_existing}
        )
        
        return import_result
    except Exception as e:
        session.rollback()
        logger.error(f"Errore nell'importazione della configurazione funnel: {e}")
        return handle_error(
            e,
            f"Errore nell'importazione della configurazione funnel",
            fallback_data={"error": True, "message": str(e)}
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
    if funnel_config.get('error', False):
        return json.dumps({'error': True, 'message': funnel_config.get('message', 'Errore sconosciuto')})
    
    # Estrai i dati se necessario
    data = funnel_config.get('data', funnel_config)
    
    # Formatta il JSON con indentazione per leggibilità
    return json.dumps(data, indent=2, ensure_ascii=False)