from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging
import json
from db.models import Step, Route, Workflow, Funnel, OrderFunnel
from utils.db_utils import get_db_session, close_db_session

# Configurazione del logging
logger = logging.getLogger(__name__)


def create_step(step_url, shopping_cart=None, post_message=False, step_code=None, gtm_reference=None):
    """Inserisce un nuovo record in funnel_manager.step.
    
    Args:
        step_url (str): URL dello step (deve essere unico).
        shopping_cart (dict, optional): Configurazione del carrello in formato JSON.
        post_message (bool, optional): Flag per abilitare i post message.
        step_code (str, optional): Codice identificativo interno dello step.
        gtm_reference (dict, optional): Riferimento GTM in formato JSON.
    
    Returns:
        dict: Dizionario contenente i dati dello step creato in caso di successo.
        dict: Dizionario contenente un messaggio di errore in caso di fallimento.
    """
    session = get_db_session()
    try:
        # Verifica se esiste già uno step con lo stesso URL
        existing_step = session.execute(
            select(Step.id).where(Step.step_url == step_url)
        ).first()
        
        if existing_step:
            return {
                'error': True,
                'message': f"Esiste già uno step con l'URL {step_url}"
            }
        
        # Prepara i dati per l'inserimento
        step_data = {
            'step_url': step_url,
            'post_message': post_message,
            'step_code': step_code
        }
        
        # Aggiungi shopping_cart e gtm_reference se forniti
        if shopping_cart:
            # Assicurati che shopping_cart sia in formato JSON
            if isinstance(shopping_cart, str):
                try:
                    shopping_cart = json.loads(shopping_cart)
                except json.JSONDecodeError:
                    return {
                        'error': True,
                        'message': "Il formato JSON di shopping_cart non è valido"
                    }
            step_data['shopping_cart'] = shopping_cart
        
        if gtm_reference:
            # Assicurati che gtm_reference sia in formato JSON
            if isinstance(gtm_reference, str):
                try:
                    gtm_reference = json.loads(gtm_reference)
                except json.JSONDecodeError:
                    return {
                        'error': True,
                        'message': "Il formato JSON di gtm_reference non è valido"
                    }
            step_data['gtm_reference'] = gtm_reference
        
        # Inserisci il nuovo step
        step_stmt = insert(Step).values(**step_data)
        step_result = session.execute(step_stmt)
        session.commit()
        
        step_id = step_result.inserted_primary_key[0]
        
        return {
            'error': False,
            'message': f"Step creato con successo",
            'step': {
                'id': step_id,
                'step_url': step_url,
                'step_code': step_code,
                'post_message': post_message
            }
        }
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Errore nella creazione dello step: {e}")
        return {
            'error': True,
            'message': f"Errore nella creazione dello step: {str(e)}"
        }
    finally:
        close_db_session(session)


def get_steps():
    """Recupera tutti gli step esistenti.
    
    Returns:
        list: Lista di dizionari contenenti i dati degli step.
        None: In caso di errore.
    """
    try:
        session = get_db_session()
        steps = session.execute(
            select(Step.id, Step.step_url, Step.step_code, Step.post_message)
            .order_by(Step.step_url)
        ).all()
        
        # Converti i risultati in una lista di dizionari
        result = [{
            'id': step.id,
            'step_url': step.step_url,
            'step_code': step.step_code,
            'post_message': step.post_message
        } for step in steps]
        
        return result
    except SQLAlchemyError as e:
        logger.error(f"Errore nel recupero degli step: {e}")
        return None
    finally:
        close_db_session(session)


def get_steps_for_workflow(workflow_id):
    """Recupera gli step associati alle route di un dato workflow.
    
    Args:
        workflow_id (int): ID del workflow.
    
    Returns:
        list: Lista di dizionari contenenti i dati degli step associati al workflow.
        None: In caso di errore.
    """
    try:
        session = get_db_session()
        
        # Recupera tutti gli step associati alle route del workflow
        # Sia come step di partenza (fromstep_id) che come step di destinazione (nextstep_id)
        from_steps = session.execute(
            select(Step.id, Step.step_url, Step.step_code, Step.post_message)
            .join(Route, Route.fromstep_id == Step.id)
            .where(Route.workflow_id == workflow_id)
            .distinct()
        ).all()
        
        next_steps = session.execute(
            select(Step.id, Step.step_url, Step.step_code, Step.post_message)
            .join(Route, Route.nextstep_id == Step.id)
            .where(Route.workflow_id == workflow_id)
            .distinct()
        ).all()
        
        # Unisci i risultati e rimuovi i duplicati
        steps_dict = {}
        for step in from_steps + next_steps:
            if step.id not in steps_dict:
                steps_dict[step.id] = {
                    'id': step.id,
                    'step_url': step.step_url,
                    'step_code': step.step_code,
                    'post_message': step.post_message
                }
        
        return list(steps_dict.values())
    except SQLAlchemyError as e:
        logger.error(f"Errore nel recupero degli step per il workflow {workflow_id}: {e}")
        return None
    finally:
        close_db_session(session)


def update_step(step_id, step_url=None, shopping_cart=None, post_message=None, step_code=None, gtm_reference=None):
    """Aggiorna un record esistente in funnel_manager.step.
    
    Args:
        step_id (int): ID dello step da aggiornare.
        step_url (str, optional): Nuovo URL dello step (deve essere unico).
        shopping_cart (dict, optional): Nuova configurazione del carrello in formato JSON.
        post_message (bool, optional): Nuovo valore per il flag post message.
        step_code (str, optional): Nuovo codice identificativo interno dello step.
        gtm_reference (dict, optional): Nuovo riferimento GTM in formato JSON.
    
    Returns:
        dict: Dizionario contenente i dati dello step aggiornato in caso di successo.
        dict: Dizionario contenente un messaggio di errore in caso di fallimento.
    """
    session = get_db_session()
    try:
        # Verifica se lo step esiste
        step = session.execute(
            select(Step).where(Step.id == step_id)
        ).scalar_one_or_none()
        
        if not step:
            return {
                'error': True,
                'message': f"Lo step con ID {step_id} non esiste"
            }
        
        # Prepara i dati per l'aggiornamento
        update_data = {}
        
        if step_url is not None:
            # Verifica se esiste già uno step con lo stesso URL (diverso da quello corrente)
            existing_step = session.execute(
                select(Step.id).where(Step.step_url == step_url, Step.id != step_id)
            ).first()
            
            if existing_step:
                return {
                    'error': True,
                    'message': f"Esiste già uno step con l'URL {step_url}"
                }
            
            update_data['step_url'] = step_url
        
        if post_message is not None:
            update_data['post_message'] = post_message
        
        if step_code is not None:
            update_data['step_code'] = step_code
        
        if shopping_cart is not None:
            # Assicurati che shopping_cart sia in formato JSON
            if isinstance(shopping_cart, str):
                try:
                    shopping_cart = json.loads(shopping_cart)
                except json.JSONDecodeError:
                    return {
                        'error': True,
                        'message': "Il formato JSON di shopping_cart non è valido"
                    }
            update_data['shopping_cart'] = shopping_cart
        
        if gtm_reference is not None:
            # Assicurati che gtm_reference sia in formato JSON
            if isinstance(gtm_reference, str):
                try:
                    gtm_reference = json.loads(gtm_reference)
                except json.JSONDecodeError:
                    return {
                        'error': True,
                        'message': "Il formato JSON di gtm_reference non è valido"
                    }
            update_data['gtm_reference'] = gtm_reference
        
        # Se non ci sono dati da aggiornare, restituisci un messaggio
        if not update_data:
            return {
                'error': False,
                'message': "Nessun dato da aggiornare",
                'step': {
                    'id': step.id,
                    'step_url': step.step_url,
                    'step_code': step.step_code,
                    'post_message': step.post_message
                }
            }
        
        # Aggiorna lo step
        session.execute(
            update(Step).where(Step.id == step_id).values(**update_data)
        )
        session.commit()
        
        # Recupera lo step aggiornato
        updated_step = session.execute(
            select(Step.id, Step.step_url, Step.step_code, Step.post_message)
            .where(Step.id == step_id)
        ).first()
        
        return {
            'error': False,
            'message': f"Step aggiornato con successo",
            'step': {
                'id': updated_step.id,
                'step_url': updated_step.step_url,
                'step_code': updated_step.step_code,
                'post_message': updated_step.post_message
            }
        }
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Errore nell'aggiornamento dello step: {e}")
        return {
            'error': True,
            'message': f"Errore nell'aggiornamento dello step: {str(e)}"
        }
    finally:
        close_db_session(session)


def delete_step(step_id):
    """Elimina un record da funnel_manager.step.
    
    Args:
        step_id (int): ID dello step da eliminare.
    
    Returns:
        dict: Dizionario contenente un messaggio di successo in caso di successo.
        dict: Dizionario contenente un messaggio di errore in caso di fallimento.
    """
    session = get_db_session()
    try:
        # Verifica se lo step esiste
        step = session.execute(
            select(Step).where(Step.id == step_id)
        ).scalar_one_or_none()
        
        if not step:
            return {
                'error': True,
                'message': f"Lo step con ID {step_id} non esiste"
            }
        
        # Verifica se lo step è utilizzato in qualche route
        routes = session.execute(
            select(Route.id)
            .where((Route.fromstep_id == step_id) | (Route.nextstep_id == step_id))
        ).all()
        
        if routes:
            return {
                'error': True,
                'message': f"Impossibile eliminare lo step: è utilizzato in {len(routes)} route. Elimina prima le route associate."
            }
        
        # Elimina lo step
        session.execute(
            delete(Step).where(Step.id == step_id)
        )
        session.commit()
        
        return {
            'error': False,
            'message': f"Step eliminato con successo"
        }
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Errore nell'eliminazione dello step: {e}")
        return {
            'error': True,
            'message': f"Errore nell'eliminazione dello step: {str(e)}"
        }
    finally:
        close_db_session(session)


def get_steps_by_funnel(funnel_id):
    """
    Recupera gli step associati a un funnel specifico.
    
    Args:
        funnel_id (int): ID del funnel.
    
    Returns:
        list: Lista di dizionari contenenti i dati degli step associati al funnel.
        None: In caso di errore.
    """
    try:
        session = get_db_session()
        
        # Prima recupera il workflow associato al funnel
        funnel = session.execute(
            select(Funnel.workflow_id).where(Funnel.id == funnel_id)
        ).scalar_one_or_none()
        
        if not funnel:
            logger.warning(f"Funnel con ID {funnel_id} non trovato")
            return []
        
        workflow_id = funnel
        
        # Recupera gli step associati al workflow del funnel
        steps = get_steps_for_workflow(workflow_id)
        
        # Se non ci sono step associati al workflow, restituisci una lista vuota
        if not steps:
            return []
            
        # Recupera gli ordini dei passi dal database per questo funnel
        order_funnels = session.execute(
            select(OrderFunnel).where(OrderFunnel.funnel_id == funnel_id)
        ).scalars().all()
        
        # Crea un dizionario di ordini per step
        order_map = {}
        for order_funnel in order_funnels:
            if order_funnel.next_step:
                order_map[order_funnel.next_step] = {
                    'order': len(order_map) + 1,
                    'name': f"Step {len(order_map) + 1}"
                }
        
        # Assegna ordini e nomi agli step
        result = []
        for step in steps:
            step_data = {
                'id': step['id'],
                'step_url': step['step_url'],
                'step_code': step['step_code'],
                'post_message': step['post_message'],
                'order': 999,  # Default alto per gli step senza ordine
                'name': step['step_code'] or f"Step {step['id']}"
            }
            
            # Se lo step ha un ordine specifico, usalo
            if step['id'] in order_map:
                step_data['order'] = order_map[step['id']]['order']
                step_data['name'] = order_map[step['id']]['name']
            
            result.append(step_data)
        
        # Ordina gli step per il campo 'order'
        result.sort(key=lambda x: x['order'])
        
        return result
    except SQLAlchemyError as e:
        logger.error(f"Errore nel recupero degli step per il funnel {funnel_id}: {e}")
        return []
    finally:
        close_db_session(session)