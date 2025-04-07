from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging
from db.models import Workflow, Funnel, Product
from utils.db_utils import get_db_session, close_db_session
from utils.config import APP_CONFIG
from utils.error_handler import handle_error, log_operation
from typing import Dict, List, Any, Optional, Union

# Configurazione del logging
logger = logging.getLogger(__name__)


def get_products() -> List[Dict[str, Any]]:
    """
    Recupera tutti i prodotti dal database.
    
    Returns:
        List[Dict[str, Any]]: Lista di dizionari contenenti i dati dei prodotti.
    """
    session = get_db_session()
    try:
        log_operation("Recupero prodotti", level=logging.INFO)
        products = session.execute(
            select(
                Product.id,
                Product.product_code,
                Product.product_description,
                Product.title_prod
            ).order_by(Product.title_prod)
        ).all()
        
        result = []
        for product in products:
            result.append({
                'id': product.id,
                'code': product.product_code,
                'description': product.product_description,
                'title': product.title_prod or product.product_description or product.product_code
            })
        
        log_operation("Recupero prodotti", {"count": len(result)})
        return result
    except Exception as e:
        return handle_error(
            e,
            "Errore durante il recupero dei prodotti",
            fallback_data=[]
        ).get('data', [])
    finally:
        close_db_session(session)


def get_funnel_by_product_id(product_id: int) -> Optional[Dict[str, Any]]:
    """
    Recupera il funnel associato a un prodotto specifico.
    
    Args:
        product_id (int): ID del prodotto.
        
    Returns:
        Optional[Dict[str, Any]]: Dizionario contenente i dati del funnel o None se non trovato.
    """
    session = get_db_session()
    try:
        log_operation("Recupero funnel per prodotto", {"product_id": product_id})
        
        # Join tra Funnel e Workflow per ottenere i dati necessari
        result = session.execute(
            select(
                Funnel.id, 
                Funnel.name, 
                Funnel.workflow_id,
                Funnel.broker_id,
                Workflow.description.label('workflow_description')
            ).join(
                Workflow, Funnel.workflow_id == Workflow.id
            ).where(
                Funnel.product_id == product_id
            )
        ).first()
        
        if result:
            funnel_data = {
                'id': result.id,
                'name': result.name,
                'workflow_id': result.workflow_id,
                'broker_id': result.broker_id,
                'workflow_description': result.workflow_description
            }
            log_operation("Funnel trovato", {"funnel_id": result.id})
            return funnel_data
        
        log_operation("Nessun funnel trovato", {"product_id": product_id}, level=logging.INFO)
        return None
    except Exception as e:
        return handle_error(
            e, 
            f"Errore durante il recupero del funnel per il prodotto {product_id}",
            fallback_data=None
        ).get('data')
    finally:
        close_db_session(session)


def create_product_funnel(product_id: int, product_name: str, default_broker_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Crea un nuovo funnel per il prodotto specificato.
    
    Args:
        product_id (int): ID del prodotto.
        product_name (str): Nome del prodotto.
        default_broker_id (int, optional): ID del broker di default. Se non specificato, viene utilizzato
                                          il valore configurato in APP_CONFIG.
    
    Returns:
        Dict[str, Any]: Dizionario contenente i dati del funnel creato o un messaggio di errore.
    """
    if default_broker_id is None:
        default_broker_id = APP_CONFIG['default_broker_id']
    
    # Verifica se esiste già un funnel per questo prodotto
    existing_funnel = get_funnel_by_product_id(product_id)
    if existing_funnel:
        log_operation("Funnel già esistente", 
                     {"product_id": product_id, "funnel_id": existing_funnel['id']}, 
                     level=logging.WARNING)
        return {
            'error': True,
            'message': f"Esiste già un funnel per il prodotto {product_name} (ID: {product_id})",
            'funnel': existing_funnel
        }
    
    log_operation("Creazione nuovo funnel", 
                 {"product_id": product_id, "product_name": product_name},
                 level=logging.INFO)
    
    session = get_db_session()
    try:
        # Inizia una transazione
        session.begin()
        
        # Crea un nuovo workflow
        workflow_description = f"Workflow per {product_name}"
        workflow_stmt = insert(Workflow).values(description=workflow_description)
        workflow_result = session.execute(workflow_stmt)
        workflow_id = workflow_result.inserted_primary_key[0]
        
        # Crea un nuovo funnel
        funnel_name = f"Funnel - {product_name}"
        funnel_stmt = insert(Funnel).values(
            workflow_id=workflow_id,
            broker_id=default_broker_id,
            name=funnel_name,
            product_id=product_id
        )
        funnel_result = session.execute(funnel_stmt)
        funnel_id = funnel_result.inserted_primary_key[0]
        
        # Commit della transazione
        session.commit()
        
        funnel_data = {
            'id': funnel_id,
            'name': funnel_name,
            'workflow_id': workflow_id
        }
        
        log_operation("Funnel creato con successo", funnel_data, success=True)
        
        return {
            'error': False,
            'message': f"Funnel creato con successo per il prodotto {product_name}",
            'funnel': funnel_data
        }
    except IntegrityError as e:
        session.rollback()
        return handle_error(
            e,
            f"Errore di integrità nella creazione del funnel: il prodotto potrebbe già avere un funnel associato",
            log_level=logging.ERROR
        )
    except SQLAlchemyError as e:
        session.rollback()
        return handle_error(
            e,
            f"Errore nella creazione del funnel",
            log_level=logging.ERROR
        )
    except Exception as e:
        session.rollback()
        return handle_error(
            e,
            f"Errore imprevisto durante la creazione del funnel",
            log_level=logging.ERROR
        )
    finally:
        close_db_session(session)