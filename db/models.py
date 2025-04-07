import logging
import os

from dotenv import load_dotenv
from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker

# Configurazione del logging
logger = logging.getLogger(__name__)

Base = declarative_base()


# Funzione per inizializzare la connessione al database
def init_connection():
    """
    Inizializza e restituisce una connessione al database.

    Returns:
        Engine: Oggetto SQLAlchemy engine per la connessione al database o None in caso di errore
    """
    try:
        # Carica le variabili d'ambiente dal file .env
        load_dotenv()

        # Ottieni le configurazioni di connessione dalle variabili d'ambiente o usa valori di default
        db_user = os.environ.get("DB_USER", "postgres")
        db_password = os.environ.get("DB_PASSWORD", "postgres")
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        db_name = os.environ.get("DB_NAME", "funnel_manager")

        # Costruisci la stringa di connessione
        connection_string = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )

        # Crea l'engine di connessione
        engine = create_engine(connection_string, echo=False)

        # Testa la connessione direttamente qui invece di importare test_connection
        try:
            # Usa l'engine per eseguire una query semplice
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connessione al database stabilita con successo")

            # Crea e configura la sessione
            session_factory = sessionmaker(bind=engine)
            Session = scoped_session(session_factory)

            return engine
        except Exception as e:
            logger.error(f"Errore nel test della connessione al database: {str(e)}")
            return None

    except Exception as e:
        logger.error(
            f"Errore durante l'inizializzazione della connessione al database: {str(e)}"
        )
        return None


# Product schema models
class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "product"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String, nullable=False, unique=True)
    product_description = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    recurring = Column(Boolean, nullable=False, default=False)
    external_id = Column(String)
    insurance_premium = Column(Numeric(10, 4))
    insurance_company = Column(String)
    insurance_company_logo = Column(String)
    business = Column(String)
    title_prod = Column(String)
    short_description = Column(String)
    description = Column(String)
    conditions = Column(String)
    information_package = Column(String)
    conditions_package = Column(String)
    display_price = Column(String)
    price = Column(Numeric(10, 4))
    only_contractor = Column(Boolean)
    maximum_insurable = Column(Numeric)
    can_open_claim = Column(Boolean)
    holder_maximum_age = Column(Numeric)
    holder_minimum_age = Column(Numeric)
    show_in_dashboard = Column(Boolean)
    product_image_id = Column(
        Integer, ForeignKey("product.product_images.id"), nullable=False
    )
    catalog_id = Column(Integer)
    properties = Column(JSONB)
    quotator_type = Column(String)
    show_addons_in_shopping_cart = Column(Boolean)
    thumbnail = Column(Boolean)
    privacy_documentation_link = Column(String)
    informative_set = Column(String)
    attachment_3_4 = Column(String)
    extras = Column(JSONB)
    plan_id = Column(String)
    plan_name = Column(String)
    duration = Column(Integer)
    product_type = Column(String)
    legacy = Column(JSONB)
    duration_type = Column(String)
    medium_tax_ratio = Column(Float)
    ia_code = Column(String)
    ia_net_commission = Column(Float)


# Funnel Manager schema models
class Condition(Base):
    __tablename__ = "condition"
    __table_args__ = {"schema": "funnel_manager"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(JSONB)


class Step(Base):
    __tablename__ = "step"
    __table_args__ = {"schema": "funnel_manager"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    step_url = Column(String(255), nullable=False, unique=True)
    shopping_cart = Column(JSONB)
    post_message = Column(Boolean, default=False)
    step_code = Column(String)
    gtm_reference = Column(JSONB)

    # Relationships
    from_routes = relationship(
        "Route", foreign_keys="Route.fromstep_id", back_populates="from_step"
    )
    to_routes = relationship(
        "Route", foreign_keys="Route.nextstep_id", back_populates="next_step"
    )


class Workflow(Base):
    __tablename__ = "workflow"
    __table_args__ = {"schema": "funnel_manager"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(255))

    # Relationships
    funnels = relationship("Funnel", back_populates="workflow")
    routes = relationship("Route", back_populates="workflow")


class Funnel(Base):
    __tablename__ = "funnel"
    __table_args__ = {"schema": "funnel_manager"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id = Column(BigInteger, ForeignKey("funnel_manager.workflow.id"))
    broker_id = Column(BigInteger)
    name = Column(String(255), unique=True)
    funnel_process = Column(BigInteger)
    type = Column(String(255))
    product_id = Column(BigInteger)

    # Relationships
    workflow = relationship("Workflow", back_populates="funnels")
    order_funnels = relationship("OrderFunnel", back_populates="funnel")


class OrderFunnel(Base):
    __tablename__ = "order_funnel"
    __table_args__ = {"schema": "funnel_manager"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(255), unique=True)
    funnel_id = Column(BigInteger, ForeignKey("funnel_manager.funnel.id"))
    previous_steps = Column(JSONB)
    next_step = Column(BigInteger, ForeignKey("funnel_manager.step.id"))

    # Relationships
    funnel = relationship("Funnel", back_populates="order_funnels")


class Route(Base):
    __tablename__ = "route"
    __table_args__ = {"schema": "funnel_manager"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nextstep_id = Column(BigInteger, ForeignKey("funnel_manager.step.id"))
    fromstep_id = Column(BigInteger, ForeignKey("funnel_manager.step.id"))
    workflow_id = Column(BigInteger, ForeignKey("funnel_manager.workflow.id"))
    route_config = Column(JSONB)

    # Relationships
    next_step = relationship(
        "Step", foreign_keys=[nextstep_id], back_populates="to_routes"
    )
    from_step = relationship(
        "Step", foreign_keys=[fromstep_id], back_populates="from_routes"
    )
    workflow = relationship("Workflow", back_populates="routes")
    route_conditions = relationship("RouteCondition", back_populates="route")


class RouteCondition(Base):
    __tablename__ = "route_condition"
    __table_args__ = {"schema": "funnel_manager"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(BigInteger, ForeignKey("funnel_manager.route.id"))
    condition_id = Column(BigInteger, ForeignKey("funnel_manager.condition.id"))
    broker_id = Column(BigInteger)
    product_id = Column(BigInteger)

    # Relationships
    route = relationship("Route", back_populates="route_conditions")
    condition = relationship("Condition")


# Design schema models
class Component(Base):
    __tablename__ = "component"
    __table_args__ = {"schema": "design"}

    id = Column(BigInteger, primary_key=True)
    component_type = Column(String, nullable=False)

    # Relationships
    component_sections = relationship("ComponentSection", back_populates="component")


class Section(Base):
    __tablename__ = "section"
    __table_args__ = {"schema": "design"}

    id = Column(BigInteger, primary_key=True)
    sectiontype = Column(String, nullable=False)

    # Relationships
    step_sections = relationship("StepSection", back_populates="section")
    component_sections = relationship("ComponentSection", back_populates="section")


class Structure(Base):
    __tablename__ = "structure"
    __table_args__ = {"schema": "design"}

    id = Column(BigInteger, primary_key=True)
    data = Column(JSON, nullable=False)

    # Relationships
    structure_component_sections = relationship(
        "StructureComponentSection", back_populates="structure"
    )


class ComponentSection(Base):
    __tablename__ = "component_section"
    __table_args__ = {"schema": "design"}

    id = Column(BigInteger, primary_key=True)
    componentid = Column(BigInteger, ForeignKey("design.component.id"), nullable=False)
    sectionid = Column(BigInteger, ForeignKey("design.section.id"), nullable=False)
    order = Column(Integer, nullable=False)
    key_cms = Column(String)

    # Relationships
    component = relationship("Component", back_populates="component_sections")
    section = relationship("Section", back_populates="component_sections")
    structure_component_sections = relationship(
        "StructureComponentSection", back_populates="component_section"
    )


class StepSection(Base):
    __tablename__ = "step_section"
    __table_args__ = {"schema": "design"}

    id = Column(BigInteger, primary_key=True)
    order = Column(Integer, nullable=False)
    sectionid = Column(BigInteger, ForeignKey("design.section.id"), nullable=False)
    stepid = Column(Integer, nullable=False)
    productid = Column(Integer)
    brokerid = Column(Integer)
    orderfieldsstepschema = Column(JSON)
    authorized = Column(Boolean, default=False)

    # Relationships
    section = relationship("Section", back_populates="step_sections")


class StructureComponentSection(Base):
    __tablename__ = "structure_component_section"
    __table_args__ = {"schema": "design"}

    id = Column(BigInteger, primary_key=True)
    component_sectionid = Column(
        BigInteger, ForeignKey("design.component_section.id"), nullable=False
    )
    structureid = Column(BigInteger, ForeignKey("design.structure.id"), nullable=False)
    order = Column(Integer, nullable=False)

    # Relationships
    component_section = relationship(
        "ComponentSection", back_populates="structure_component_sections"
    )
    structure = relationship("Structure", back_populates="structure_component_sections")
    cms_keys = relationship("CmsKey", back_populates="structure_component_section")


class CmsKey(Base):
    __tablename__ = "cms_key"
    __table_args__ = {"schema": "design"}

    id = Column(BigInteger, primary_key=True)
    value = Column(JSON, nullable=False)
    structurecomponentsectionid = Column(
        BigInteger, ForeignKey("design.structure_component_section.id"), nullable=False
    )

    # Relationships
    structure_component_section = relationship(
        "StructureComponentSection", back_populates="cms_keys"
    )
