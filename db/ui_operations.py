import logging
import json
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import func, desc
from db.models import (
    Section, Component, StepSection, ComponentSection, 
    Structure, StructureComponentSection, CmsKey
)
from utils.db_utils import get_db_session, close_db_session

# Configurazione del logging
logger = logging.getLogger(__name__)

# Operazioni per le sezioni
def create_section(sectiontype):
    """
    Crea una nuova sezione nel database
    
    Args:
        sectiontype (str): Tipo di sezione
        
    Returns:
        dict: Dizionario con il risultato dell'operazione
    """
    session = get_db_session()
    try:
        # Verifica se esiste già una sezione con lo stesso tipo
        existing_section = session.query(Section).filter(
            Section.sectiontype == sectiontype
        ).first()
        
        if existing_section:
            return {
                'error': True,
                'message': f"Esiste già una sezione con il tipo '{sectiontype}'",
                'section': {
                    'id': existing_section.id,
                    'sectiontype': existing_section.sectiontype
                }
            }
        
        # Crea una nuova sezione
        new_section = Section(sectiontype=sectiontype)
        session.add(new_section)
        session.commit()
        
        return {
            'error': False,
            'message': f"Sezione '{sectiontype}' creata con successo",
            'section': {
                'id': new_section.id,
                'sectiontype': new_section.sectiontype
            }
        }
        
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Errore nella creazione della sezione: {error_message}")
        return {
            'error': True,
            'message': f"Errore nella creazione della sezione: {error_message}"
        }
    finally:
        session.close()

def get_sections():
    """
    Recupera tutte le sezioni dal database
    
    Returns:
        list: Lista di dizionari contenenti i dati delle sezioni
    """
    session = get_db_session()
    try:
        sections = session.query(Section).all()
        
        result = []
        for section in sections:
            result.append({
                'id': section.id,
                'sectiontype': section.sectiontype
            })
            
        return result
        
    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(f"Errore nel recupero delle sezioni: {error_message}")
        return []
    finally:
        session.close()

# Operazioni per i componenti
def create_component(component_type):
    """
    Crea un nuovo componente nel database
    
    Args:
        component_type (str): Tipo di componente
        
    Returns:
        dict: Dizionario con il risultato dell'operazione
    """
    session = get_db_session()
    try:
        # Verifica se esiste già un componente con lo stesso tipo
        existing_component = session.query(Component).filter(
            Component.component_type == component_type
        ).first()
        
        if existing_component:
            return {
                'error': True,
                'message': f"Esiste già un componente con il tipo '{component_type}'",
                'component': {
                    'id': existing_component.id,
                    'component_type': existing_component.component_type
                }
            }
        
        # Crea un nuovo componente
        new_component = Component(component_type=component_type)
        session.add(new_component)
        session.commit()
        
        return {
            'error': False,
            'message': f"Componente '{component_type}' creato con successo",
            'component': {
                'id': new_component.id,
                'component_type': new_component.component_type
            }
        }
        
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Errore nella creazione del componente: {error_message}")
        return {
            'error': True,
            'message': f"Errore nella creazione del componente: {error_message}"
        }
    finally:
        session.close()

def get_components():
    """
    Recupera tutti i componenti dal database
    
    Returns:
        list: Lista di dizionari contenenti i dati dei componenti
    """
    session = get_db_session()
    try:
        components = session.query(Component).all()
        
        result = []
        for component in components:
            result.append({
                'id': component.id,
                'component_type': component.component_type
            })
            
        return result
        
    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(f"Errore nel recupero dei componenti: {error_message}")
        return []
    finally:
        session.close()

# Operazioni per l'associazione di sezioni a step
def add_section_to_step(step_id, section_id, order, product_id=None, broker_id=None):
    """
    Associa una sezione a uno step
    
    Args:
        step_id (int): ID dello step
        section_id (int): ID della sezione
        order (int): Ordine della sezione nello step
        product_id (int, optional): ID del prodotto per personalizzazione
        broker_id (int, optional): ID del broker per personalizzazione
        
    Returns:
        dict: Dizionario con il risultato dell'operazione
    """
    session = get_db_session()
    try:
        # Verifica se esiste già un'associazione tra la sezione e lo step
        existing_association = session.query(StepSection).filter(
            StepSection.stepid == step_id,
            StepSection.sectionid == section_id,
            StepSection.productid == product_id,
            StepSection.brokerid == broker_id
        ).first()
        
        if existing_association:
            return {
                'error': True,
                'message': "Questa sezione è già associata a questo step",
                'step_section': {
                    'id': existing_association.id,
                    'order': existing_association.order
                }
            }
        
        # Crea una nuova associazione
        new_association = StepSection(
            stepid=step_id,
            sectionid=section_id,
            order=order,
            authorized=True,  # Default a True
            productid=product_id,
            brokerid=broker_id
        )
        session.add(new_association)
        session.commit()
        
        return {
            'error': False,
            'message': "Sezione associata allo step con successo",
            'step_section': {
                'id': new_association.id,
                'order': new_association.order
            }
        }
        
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Errore nell'associazione della sezione allo step: {error_message}")
        return {
            'error': True,
            'message': f"Errore nell'associazione della sezione allo step: {error_message}"
        }
    finally:
        session.close()

def get_sections_for_step(step_id, product_id=None, broker_id=None):
    """
    Recupera tutte le sezioni associate a uno step specifico.
    
    Args:
        step_id (int): ID dello step
        product_id (int, optional): ID del prodotto per filtrare le sezioni
        broker_id (int, optional): ID del broker per filtrare le sezioni
        
    Returns:
        list: Lista di sezioni associate allo step in formato dizionario
    """
    session = get_db_session()
    try:
        query = session.query(
            StepSection, 
            Section
        ).join(
            Section, 
            StepSection.sectionid == Section.id
        ).filter(
            StepSection.stepid == step_id
        )
        
        # Filtra per prodotto se specificato
        if product_id is not None:
            query = query.filter(
                (StepSection.productid == product_id) | (StepSection.productid == None)
            )
            
        # Filtra per broker se specificato
        if broker_id is not None:
            query = query.filter(
                (StepSection.brokerid == broker_id) | (StepSection.brokerid == None)
            )
            
        results = query.all()
        
        sections = []
        for step_section, section in results:
            sections.append({
                'id': section.id,
                'sectiontype': section.sectiontype,
                'step_section_id': step_section.id,
                'order': step_section.order,
                'authorized': step_section.authorized,
                'product_id': step_section.productid,
                'broker_id': step_section.brokerid
            })
            
        return sections
        
    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(f"Errore nel recupero delle sezioni per lo step: {error_message}")
        return []
    finally:
        session.close()

def update_step_section_order(step_section_id, new_order):
    """
    Aggiorna l'ordine di una sezione all'interno di uno step
    
    Args:
        step_section_id (int): ID dell'associazione step-sezione
        new_order (int): Nuovo ordine della sezione
        
    Returns:
        dict: Dizionario con il risultato dell'operazione
    """
    session = get_db_session()
    try:
        step_section = session.query(StepSection).get(step_section_id)
        
        if not step_section:
            return {
                'error': True,
                'message': "Associazione sezione-step non trovata"
            }
        
        step_section.order = new_order
        session.commit()
        
        return {
            'error': False,
            'message': "Ordine della sezione aggiornato con successo",
            'step_section': {
                'id': step_section.id,
                'order': step_section.order
            }
        }
        
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Errore nell'aggiornamento dell'ordine della sezione: {error_message}")
        return {
            'error': True,
            'message': f"Errore nell'aggiornamento dell'ordine della sezione: {error_message}"
        }
    finally:
        session.close()

def delete_step_section(step_section_id):
    """
    Elimina l'associazione tra una sezione e uno step
    
    Args:
        step_section_id (int): ID dell'associazione step-sezione
        
    Returns:
        dict: Dizionario con il risultato dell'operazione
    """
    session = get_db_session()
    try:
        step_section = session.query(StepSection).get(step_section_id)
        
        if not step_section:
            return {
                'error': True,
                'message': "Associazione sezione-step non trovata"
            }
        
        session.delete(step_section)
        session.commit()
        
        return {
            'error': False,
            'message': "Sezione rimossa dallo step con successo"
        }
        
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Errore nella rimozione della sezione dallo step: {error_message}")
        return {
            'error': True,
            'message': f"Errore nella rimozione della sezione dallo step: {error_message}"
        }
    finally:
        session.close()

# Operazioni per l'associazione di componenti a sezioni
def add_component_to_section(section_id, component_id, order):
    """
    Associa un componente a una sezione
    
    Args:
        section_id (int): ID della sezione
        component_id (int): ID del componente
        order (int): Ordine del componente nella sezione
        
    Returns:
        dict: Dizionario con il risultato dell'operazione
    """
    session = get_db_session()
    try:
        # Verifica se esiste già un'associazione tra il componente e la sezione
        existing_association = session.query(ComponentSection).filter(
            ComponentSection.sectionid == section_id,
            ComponentSection.componentid == component_id
        ).first()
        
        if existing_association:
            return {
                'error': True,
                'message': "Questo componente è già associato a questa sezione",
                'component_section': {
                    'id': existing_association.id,
                    'order': existing_association.order
                }
            }
        
        # Crea una nuova associazione
        new_association = ComponentSection(
            sectionid=section_id,
            componentid=component_id,
            order=order
        )
        session.add(new_association)
        session.commit()
        
        # Crea anche una struttura vuota per questo componente-sezione
        structure = Structure(data={})
        session.add(structure)
        session.flush()  # Flush per ottenere l'ID della struttura
        
        # Associa la struttura al componente-sezione
        structure_component_section = StructureComponentSection(
            structureid=structure.id,
            componentsectionid=new_association.id
        )
        session.add(structure_component_section)
        session.commit()
        
        return {
            'error': False,
            'message': "Componente associato alla sezione con successo",
            'component_section': {
                'id': new_association.id,
                'order': new_association.order,
                'structure_id': structure.id,
                'structure_component_section_id': structure_component_section.id
            }
        }
        
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Errore nell'associazione del componente alla sezione: {error_message}")
        return {
            'error': True,
            'message': f"Errore nell'associazione del componente alla sezione: {error_message}"
        }
    finally:
        session.close()

def get_components_for_section(section_id):
    """
    Recupera tutti i componenti associati a una sezione specifica.
    
    Args:
        section_id (int): ID della sezione
        
    Returns:
        list: Lista di componenti associati alla sezione in formato dizionario
    """
    session = get_db_session()
    try:
        query = session.query(
            ComponentSection, 
            Component,
            Structure,
            StructureComponentSection
        ).join(
            Component, 
            ComponentSection.componentid == Component.id
        ).outerjoin(
            StructureComponentSection,
            ComponentSection.id == StructureComponentSection.component_sectionid
        ).outerjoin(
            Structure,
            StructureComponentSection.structureid == Structure.id
        ).filter(
            ComponentSection.sectionid == section_id
        )
            
        results = query.all()
        
        components = []
        for component_section, component, structure, structure_component_section in results:
            component_data = {
                'id': component.id,
                'component_type': component.component_type,
                'component_section_id': component_section.id,
                'order': component_section.order,
                'structure': structure.data if structure else None,
                'structure_id': structure.id if structure else None,
                'structure_component_section_id': structure_component_section.id if structure_component_section else None
            }
            components.append(component_data)
            
        return components
        
    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(f"Errore nel recupero dei componenti per la sezione: {error_message}")
        return []
    finally:
        session.close()

def update_component_section_order(component_section_id, new_order):
    """
    Aggiorna l'ordine di un componente all'interno di una sezione
    
    Args:
        component_section_id (int): ID dell'associazione componente-sezione
        new_order (int): Nuovo ordine del componente
        
    Returns:
        dict: Dizionario con il risultato dell'operazione
    """
    session = get_db_session()
    try:
        component_section = session.query(ComponentSection).get(component_section_id)
        
        if not component_section:
            return {
                'error': True,
                'message': "Associazione componente-sezione non trovata"
            }
        
        component_section.order = new_order
        session.commit()
        
        return {
            'error': False,
            'message': "Ordine del componente aggiornato con successo",
            'component_section': {
                'id': component_section.id,
                'order': component_section.order
            }
        }
        
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Errore nell'aggiornamento dell'ordine del componente: {error_message}")
        return {
            'error': True,
            'message': f"Errore nell'aggiornamento dell'ordine del componente: {error_message}"
        }
    finally:
        session.close()

def delete_component_section(component_section_id):
    """
    Elimina l'associazione tra un componente e una sezione
    
    Args:
        component_section_id (int): ID dell'associazione componente-sezione
        
    Returns:
        dict: Dizionario con il risultato dell'operazione
    """
    session = get_db_session()
    try:
        # Trova l'associazione componente-sezione
        component_section = session.query(ComponentSection).get(component_section_id)
        
        if not component_section:
            return {
                'error': True,
                'message': "Associazione componente-sezione non trovata"
            }
        
        # Trova la struttura associata a questo componente-sezione
        structure_component_section = session.query(StructureComponentSection).filter(
            StructureComponentSection.componentsectionid == component_section_id
        ).first()
        
        # Se esiste una struttura associata, trova ed elimina le chiavi CMS associate
        if structure_component_section:
            # Elimina le chiavi CMS associate a questa struttura
            cms_keys = session.query(CmsKey).filter(
                CmsKey.structurecomponentsectionid == structure_component_section.id
            ).all()
            
            for cms_key in cms_keys:
                session.delete(cms_key)
            
            # Ottieni l'ID della struttura
            structure_id = structure_component_section.structureid
            
            # Elimina l'associazione struttura-componente-sezione
            session.delete(structure_component_section)
            
            # Elimina la struttura
            structure = session.query(Structure).get(structure_id)
            if structure:
                session.delete(structure)
        
        # Infine, elimina l'associazione componente-sezione
        session.delete(component_section)
        session.commit()
        
        return {
            'error': False,
            'message': "Componente rimosso dalla sezione con successo"
        }
        
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Errore nella rimozione del componente dalla sezione: {error_message}")
        return {
            'error': True,
            'message': f"Errore nella rimozione del componente dalla sezione: {error_message}"
        }
    finally:
        session.close()

# Operazioni per le strutture
def update_structure_data(structure_id, new_data):
    """
    Aggiorna i dati di una struttura
    
    Args:
        structure_id (int): ID della struttura
        new_data (dict): Nuovi dati JSON da salvare
        
    Returns:
        dict: Dizionario con il risultato dell'operazione
    """
    session = get_db_session()
    try:
        structure = session.query(Structure).get(structure_id)
        
        if not structure:
            return {
                'error': True,
                'message': "Struttura non trovata"
            }
        
        structure.data = new_data
        session.commit()
        
        return {
            'error': False,
            'message': "Dati della struttura aggiornati con successo",
            'structure': {
                'id': structure.id,
                'data': structure.data
            }
        }
        
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Errore nell'aggiornamento dei dati della struttura: {error_message}")
        return {
            'error': True,
            'message': f"Errore nell'aggiornamento dei dati della struttura: {error_message}"
        }
    finally:
        session.close()

# Operazioni per le chiavi CMS
def create_or_update_cms_key(structure_component_section_id, cms_data):
    """
    Crea o aggiorna una chiave CMS per una struttura
    
    Args:
        structure_component_section_id (int): ID dell'associazione struttura-componente-sezione
        cms_data (dict): Dati JSON della chiave CMS
        
    Returns:
        dict: Dizionario con il risultato dell'operazione
    """
    session = get_db_session()
    try:
        # Verifica se esiste già una chiave CMS per questa associazione
        cms_key = session.query(CmsKey).filter(
            CmsKey.structurecomponentsectionid == structure_component_section_id
        ).first()
        
        if cms_key:
            # Aggiorna la chiave esistente
            cms_key.value = cms_data
            session.commit()
            
            return {
                'error': False,
                'message': "Chiave CMS aggiornata con successo",
                'cms_key': {
                    'id': cms_key.id,
                    'value': cms_key.value
                }
            }
        else:
            # Crea una nuova chiave CMS
            new_cms_key = CmsKey(
                structurecomponentsectionid=structure_component_section_id,
                value=cms_data
            )
            session.add(new_cms_key)
            session.commit()
            
            return {
                'error': False,
                'message': "Chiave CMS creata con successo",
                'cms_key': {
                    'id': new_cms_key.id,
                    'value': new_cms_key.value
                }
            }
        
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Errore nella creazione/aggiornamento della chiave CMS: {error_message}")
        return {
            'error': True,
            'message': f"Errore nella creazione/aggiornamento della chiave CMS: {error_message}"
        }
    finally:
        session.close()

def get_cms_key_for_structure(structure_component_section_id):
    """
    Recupera la chiave CMS associata a una struttura
    
    Args:
        structure_component_section_id (int): ID dell'associazione struttura-componente-sezione
        
    Returns:
        dict: Dizionario con i dati della chiave CMS o None
    """
    session = get_db_session()
    try:
        cms_key = session.query(CmsKey).filter(
            CmsKey.structurecomponentsectionid == structure_component_section_id
        ).first()
        
        if cms_key:
            return {
                'id': cms_key.id,
                'value': cms_key.value,
                'structure_component_section_id': cms_key.structurecomponentsectionid
            }
        else:
            return None
        
    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(f"Errore nel recupero della chiave CMS: {error_message}")
        return None
    finally:
        session.close()