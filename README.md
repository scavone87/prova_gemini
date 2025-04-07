# Funnel Manager Dashboard

## Panoramica

Funnel Manager Dashboard è un'applicazione web sviluppata con Streamlit per la gestione e l'analisi dei funnel di marketing. Permette di:

- Visualizzare e configurare funnel per vari prodotti
- Gestire gli step e le route tra gli step
- Visualizzare metriche e analisi delle performance dei funnel
- Esportare e importare configurazioni di funnel

## 🚀 Caratteristiche Principali

- **Dashboard Interattiva**: Visualizza metriche e statistiche sui funnel di marketing
- **Gestione Funnel**: Crea e modifica funnel associati a prodotti
- **Gestione Step**: Configura gli step dei funnel con dettagli come URL e azioni
- **Configurazione Route**: Definisci percorsi tra gli step per guidare gli utenti
- **Esportazione/Importazione**: Salva e riutilizza configurazioni di funnel
- **Interfaccia Intuitiva**: UI moderna con spinner, dialoghi di conferma e funzionalità di annullamento

## 📋 Requisiti di Sistema

- Python 3.11 o superiore
- PostgreSQL 14 o superiore
- Connessione Internet per accedere alle dipendenze

## 🔧 Installazione

### Con Docker (consigliato)

```bash
# Clona il repository
git clone https://github.com/yourcompany/funnel-manager.git
cd funnel-manager

# Costruisci l'immagine Docker
docker build -t funnel-manager .

# Esegui il container
docker run -p 8501:8501 \
  -e DB_HOST=your-db-host \
  -e DB_PORT=5432 \
  -e DB_NAME=funnel_manager \
  -e DB_USER=your-db-user \
  -e DB_PASSWORD=your-db-password \
  funnel-manager
```

### Installazione manuale

```bash
# Clona il repository
git clone https://github.com/yourcompany/funnel-manager.git
cd funnel-manager

# Crea e attiva un ambiente virtuale
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate

# Installa le dipendenze
pip install -r requirements.txt

# Configura le variabili d'ambiente
export DB_HOST=your-db-host
export DB_PORT=5432
export DB_NAME=funnel_manager
export DB_USER=your-db-user
export DB_PASSWORD=your-db-password

# Esegui le migrazioni del database
cd migrations
alembic upgrade head
cd ..

# Avvia l'applicazione
streamlit run app.py
```

## 🚀 Utilizzo Rapido

1. **Home**: La pagina iniziale mostra una panoramica del sistema con link alle varie sezioni
2. **Selezione Prodotto**: Seleziona o cerca un prodotto per cui configurare un funnel
3. **Gestione Step**: Configura gli step del funnel (URL, comportamenti, etc.)
4. **Gestione Route**: Definisci le connessioni tra gli step
5. **Esportazione/Importazione**: Esporta o importa configurazioni complete di funnel
6. **Dashboard**: Visualizza statistiche e metriche di performance dei funnel

## 📊 Struttura dell'Applicazione

```
app.py                  # Entry point dell'applicazione
Dockerfile              # Configurazione per containerizzazione
requirements.txt        # Dipendenze Python
.github/workflows/      # Pipeline CI/CD
migrations/             # Gestione migrazioni database con Alembic
pages/                  # Pagine Streamlit dell'applicazione
├── dashboard.py        # Dashboard con metriche e grafici
├── export_import.py    # Esportazione/importazione configurazioni
├── product_selection.py # Selezione prodotti
├── routes_manager.py   # Gestione delle route
├── steps_manager.py    # Gestione degli step
└── ui_configurator.py  # Configurazione UI avanzata
components/             # Componenti riutilizzabili UI
db/                     # Operazioni database e modelli
├── models.py           # Modelli SQLAlchemy
├── funnel_operations.py # Operazioni sui funnel
├── step_operations.py  # Operazioni sugli step
└── route_operations.py # Operazioni sulle route
utils/                  # Utilities
├── cache_manager.py    # Gestione della cache
├── config.py          # Configurazione centralizzata
├── db_utils.py        # Utilities database
├── error_handler.py   # Gestione centralizzata errori
└── export_import.py   # Funzioni import/export
```

## 🔄 API e Integrazione

L'applicazione si integra con:

- Database PostgreSQL per la persistenza dei dati
- Sistema di configurazione per funnel e step
- Sistema di tracciamento per dati di conversione (opzionale)

## 💡 Best Practices

- **Cache**: Usare `@st.cache_data` per ottimizzare le query frequenti
- **Invalidazione**: Invalidare la cache dopo operazioni di modifica con `st.rerun()`
- **Paginazione**: Per liste lunghe, utilizzare la paginazione integrata
- **Errori**: Catturare sempre le eccezioni con try/except e gestirle con `handle_error()`

## 🛠 Sviluppo

### Setup ambiente di sviluppo

```bash
# Installa dipendenze di sviluppo
pip install -r requirements-dev.txt

# Esegui i test
pytest

# Formatta il codice
black .
isort .

# Esegui l'analisi statica
flake8
mypy .
```

### Migrazioni del database

```bash
# Genera una nuova migrazione
cd migrations
alembic revision --autogenerate -m "descrizione della modifica"

# Applica migrazioni
alembic upgrade head
```

## 🔒 Sicurezza

- I dati sensibili devono essere sempre gestiti tramite variabili d'ambiente o Streamlit secrets
- Le password di database non devono mai essere hardcoded
- Per deployment in produzione, utilizzare HTTPS

## 📄 Licenza

Questo progetto è proprietario e confidenziale. © 2025 YourCompany Inc.