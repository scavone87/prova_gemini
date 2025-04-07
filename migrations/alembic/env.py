import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Questo è l'oggetto Alembic, usato per le operazioni di migrazione
config = context.config

# Imposta la stringa di connessione dalle variabili di ambiente
# se disponibili, altrimenti usa quella presente in alembic.ini
if (
    os.environ.get("DB_USER")
    and os.environ.get("DB_PASSWORD")
    and os.environ.get("DB_HOST")
    and os.environ.get("DB_NAME")
):
    db_url = f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}/{os.environ['DB_NAME']}"
    config.set_main_option("sqlalchemy.url", db_url)

# Interpreta il file di configurazione di logging
fileConfig(config.config_file_name)

# Aggiungi qui i modelli MetaData
# per supportare la generazione automatica delle migrazioni.
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from db.models import Base

target_metadata = Base.metadata

# Altri valori includono 'postgresql+psycopg2', 'postgresql+pg8000', 'mysql+mysqlconnector', 'sqlite+pysqlite'
dialect = "postgresql"


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Rileva cambiamenti nei tipi di colonne
            compare_server_default=True,  # Rileva cambiamenti nei valori di default
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
