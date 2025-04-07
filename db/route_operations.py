import json
import logging

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import aliased

from db.models import Route, Step, Workflow
from utils.db_utils import close_db_session, get_db_session

# Configurazione del logging
logger = logging.getLogger(__name__)


def create_route(workflow_id, from_step_id, next_step_id, route_config=None):
    """Inserisce un nuovo record in funnel_manager.route.

    Args:
        workflow_id (int): ID del workflow a cui associare la route.
        from_step_id (int): ID dello step di partenza.
        next_step_id (int): ID dello step di destinazione.
        route_config (dict, optional): Configurazione della route in formato JSON.

    Returns:
        dict: Dizionario contenente i dati della route creata in caso di successo.
        dict: Dizionario contenente un messaggio di errore in caso di fallimento.
    """
    session = get_db_session()
    try:
        # Verifica se il workflow esiste
        workflow = session.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        ).scalar_one_or_none()

        if not workflow:
            return {
                "error": True,
                "message": f"Il workflow con ID {workflow_id} non esiste",
            }

        # Verifica se gli step esistono
        if from_step_id is not None:
            from_step = session.execute(
                select(Step).where(Step.id == from_step_id)
            ).scalar_one_or_none()

            if not from_step:
                return {
                    "error": True,
                    "message": f"Lo step di partenza con ID {from_step_id} non esiste",
                }

        next_step = session.execute(
            select(Step).where(Step.id == next_step_id)
        ).scalar_one_or_none()

        if not next_step:
            return {
                "error": True,
                "message": f"Lo step di destinazione con ID {next_step_id} non esiste",
            }

        # Verifica se esiste già una route identica
        existing_route = session.execute(
            select(Route.id).where(
                (Route.workflow_id == workflow_id)
                & (Route.fromstep_id == from_step_id)
                & (Route.nextstep_id == next_step_id)
            )
        ).first()

        if existing_route:
            return {
                "error": True,
                "message": f"Esiste già una route identica per questo workflow",
            }

        # Prepara i dati per l'inserimento
        route_data = {
            "workflow_id": workflow_id,
            "fromstep_id": from_step_id,
            "nextstep_id": next_step_id,
        }

        # Aggiungi route_config se fornito
        if route_config:
            # Assicurati che route_config sia in formato JSON
            if isinstance(route_config, str):
                try:
                    route_config = json.loads(route_config)
                except json.JSONDecodeError:
                    return {
                        "error": True,
                        "message": "Il formato JSON di route_config non è valido",
                    }
            route_data["route_config"] = route_config

        # Inserisci la nuova route
        route_stmt = insert(Route).values(**route_data)
        route_result = session.execute(route_stmt)
        session.commit()

        route_id = route_result.inserted_primary_key[0]

        return {
            "error": False,
            "message": f"Route creata con successo",
            "route": {
                "id": route_id,
                "workflow_id": workflow_id,
                "from_step_id": from_step_id,
                "next_step_id": next_step_id,
            },
        }
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Errore nella creazione della route: {e}")
        return {
            "error": True,
            "message": f"Errore nella creazione della route: {str(e)}",
        }
    finally:
        close_db_session(session)


def get_routes_for_workflow(workflow_id):
    """Recupera tutte le route associate a un workflow.

    Args:
        workflow_id (int): ID del workflow.

    Returns:
        list: Lista di dizionari contenenti i dati delle route associate al workflow.
        None: In caso di errore.
    """
    try:
        session = get_db_session()

        # Recupera tutte le route del workflow con i dati degli step associati
        # Definiamo esplicitamente l'alias per il next_step
        next_step_alias = aliased(Step, name="next_step_alias")

        routes = session.execute(
            select(
                Route.id,
                Route.workflow_id,
                Route.fromstep_id,
                Route.nextstep_id,
                Route.route_config,
                Step.step_url.label("from_step_url"),
                Step.step_code.label("from_step_code"),
                next_step_alias.step_url.label("next_step_url"),
                next_step_alias.step_code.label("next_step_code"),
            )
            .join(Step, Step.id == Route.fromstep_id, isouter=True)
            .join(
                next_step_alias, next_step_alias.id == Route.nextstep_id, isouter=True
            )
            .where(Route.workflow_id == workflow_id)
            .order_by(Route.id)
        ).all()

        # Converti i risultati in una lista di dizionari
        result = [
            {
                "id": route.id,
                "workflow_id": route.workflow_id,
                "from_step": {
                    "id": route.fromstep_id,
                    "url": route.from_step_url,
                    "code": route.from_step_code,
                },
                "next_step": {
                    "id": route.nextstep_id,
                    "url": route.next_step_url,
                    "code": route.next_step_code,
                },
                "route_config": route.route_config,
            }
            for route in routes
        ]

        return result
    except SQLAlchemyError as e:
        logger.error(
            f"Errore nel recupero delle route per il workflow {workflow_id}: {e}"
        )
        return None
    finally:
        close_db_session(session)


def delete_route(route_id):
    """Elimina una route.

    Args:
        route_id (int): ID della route da eliminare.

    Returns:
        dict: Dizionario contenente un messaggio di successo in caso di successo.
        dict: Dizionario contenente un messaggio di errore in caso di fallimento.
    """
    session = get_db_session()
    try:
        # Verifica se la route esiste
        route = session.execute(
            select(Route).where(Route.id == route_id)
        ).scalar_one_or_none()

        if not route:
            return {"error": True, "message": f"La route con ID {route_id} non esiste"}

        # Elimina la route
        session.execute(delete(Route).where(Route.id == route_id))
        session.commit()

        return {"error": False, "message": f"Route eliminata con successo"}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Errore nell'eliminazione della route: {e}")
        return {
            "error": True,
            "message": f"Errore nell'eliminazione della route: {str(e)}",
        }
    finally:
        close_db_session(session)
