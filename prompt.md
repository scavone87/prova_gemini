Titolo del Progetto: Dashboard Streamlit Funnel Manager

Obiettivo Generale:

Sviluppare una dashboard interattiva e intuitiva con Streamlit per semplificare e guidare la creazione e gestione di funnel di marketing. L'obiettivo principale è astrarre la complessità del database sottostante e fornire un'interfaccia "a prova di stupido" per consentire anche a utenti non esperti di database (come sviluppatori frontend o team marketing) di configurare funnel efficaci in modo autonomo e senza errori. Questa dashboard mira a democratizzare la creazione di funnel, rendendola accessibile a chiunque, indipendentemente dalle proprie competenze tecniche.

Utente Target:

Sviluppatori frontend, team marketing, content manager e chiunque necessiti di creare e gestire funnel di marketing senza avere competenze dirette di gestione database. La dashboard deve essere estremamente user-friendly e guidata, riducendo al minimo la possibilità di errore e la necessità di conoscenza tecnica del backend. L'utente target ideale è colui che ha bisogno di uno strumento potente ma semplice da usare, che lo guidi passo passo nella creazione del funnel senza richiedere una curva di apprendimento ripida.

Funzionalità Chiave (MVP - Minimum Viable Product):

Selezione Prodotto:

Interfaccia per selezionare un prodotto esistente da un elenco (popolato dinamicamente dal database product.products). L'interfaccia dovrebbe permettere una ricerca e/o filtro efficiente tra i prodotti, specialmente se l'elenco diventa ampio.

Creazione Funnel Prodotto (Automatizzata):

Pulsante "Crea Funnel per Prodotto selezionato" che esegue automaticamente le seguenti operazioni in background:

Crea una nuova istanza di funnel_manager.workflow con una descrizione predefinita basata sul nome del prodotto. La descrizione dovrebbe essere facilmente identificabile e modificabile in futuro, se necessario.

Crea una nuova istanza di funnel_manager.funnel associata al workflow appena creato, al product_id selezionato e a un broker_id di default (da configurare). Il broker_id di default dovrebbe essere configurabile a livello di sistema o prodotto, offrendo flessibilità.

Gestione Step del Funnel:

Interfaccia per creare nuovi funnel_manager.step definendo:

step_url (obbligatorio e univoco). Dovrebbe esserci una validazione in tempo reale per garantire l'univocità dell'URL e suggerimenti per formati validi.

shopping_cart (JSON, opzionale). Fornire un editor JSON con validazione di sintassi e magari esempi o schemi predefiniti.

post_message (checkbox). Aggiungere un help text contestuale che spieghi l'utilizzo di post_message.

step_code (testo, opzionale). Spiegare l'utilità del step_code (es. identificazione interna, tracking).

gtm_reference (JSON, opzionale). Come per shopping_cart, fornire un editor JSON con validazione e esempi.

Interfaccia per selezionare step esistenti. L'interfaccia di selezione step dovrebbe essere chiara e permettere la ricerca o il filtro per URL o Step Code.

Visualizzazione degli step creati in una lista chiara. La lista di step dovrebbe essere ordinabile e filtrabile, e mostrare informazioni chiave come URL e Step Code.

Funzionalità per definire le funnel_manager.route direttamente dall'interfaccia degli step, collegando uno step ad un altro all'interno del workflow del funnel. Interfaccia intuitiva per la creazione di route (es. selectbox "Route da Step X a Step Y"). Esplorare anche interfacce visuali come diagrammi di flusso semplificati per la gestione delle route, oltre ai selectbox.

Configurazione UI Step (Sezioni e Componenti Automatica):

Per ogni step selezionato, interfaccia per gestire le sezioni UI (design.section). L'interfaccia dovrebbe mostrare le sezioni già associate allo step e permettere di ordinarle.

Possibilità di creare nuove design.section definendo sectiontype. Suggerire dei sectiontype comuni (es. Header, Body, Footer, Banner) come placeholder o esempi per guidare l'utente.

Possibilità di selezionare design.section esistenti. L'interfaccia di selezione section dovrebbe permettere la ricerca e il filtro per sectiontype.

Creazione automatica di design.step_section quando una sezione viene associata ad uno step. L'ordine delle sezioni nello step deve essere configurabile (ordine di visualizzazione). L'ordinamento delle sezioni dovrebbe essere intuitivo, idealmente tramite drag-and-drop o frecce di ordinamento.

Per ogni sezione all'interno di uno step:

Interfaccia per gestire i componenti UI (design.component). L'interfaccia dovrebbe mostrare i componenti già associati alla sezione e permettere di ordinarli.

Possibilità di creare nuovi design.component definendo component_type. Suggerire dei component_type comuni (es. Banner, Form, Video, Testo, Immagine) come placeholder o esempi.

Possibilità di selezionare design.component esistenti. L'interfaccia di selezione component dovrebbe permettere la ricerca e il filtro per component_type.

Creazione automatica di design.component_section e design.structure_component_section (con design.structure iniziale vuota) quando un componente viene associato ad una sezione. L'ordine dei componenti nella sezione deve essere configurabile. Come per le sezioni, l'ordinamento dei componenti dovrebbe essere intuitivo (drag-and-drop o frecce).

Interfaccia per configurare design.structure.data (JSON editor) per ogni componente-sezione. Utilizzare un editor JSON avanzato con validazione, auto-completamento (se possibile), e magari la possibilità di definire schemi JSON per i dati della struttura.

Interfaccia per configurare design.cms_key (JSON editor chiave-valore) per ogni structure-component-section. Fornire un editor JSON intuitivo per coppie chiave-valore, con la possibilità di aggiungere e rimuovere coppie dinamicamente.

Visualizzazione e Feedback:

Feedback chiaro all'utente per ogni operazione (successo, errore, avvisi). Utilizzare colori distinti (verde per successo, rosso per errore, giallo per avviso) e messaggi contestuali chiari.

Visualizzazione delle entità create e delle relazioni (es. lista di step, route definite, sezioni associate a step, componenti associati a sezioni). Esplorare la possibilità di visualizzazioni grafiche delle relazioni tra entità, come diagrammi ad albero o grafi, per rendere la struttura più comprensibile. Considerare anche un pannello di riepilogo che mostri la configurazione corrente del funnel in modo conciso.

Requisiti Tecnici:

Linguaggio di Programmazione: Python

Framework UI: Streamlit

Database: PostgreSQL (integrazione REALE, non simulazioni in memoria per la versione finale). Garantire una connessione sicura e efficiente al database. Considerare l'uso di connection pooling.

Librerie Python: streamlit, psycopg2 (o libreria ORM come SQLAlchemy - opzionale ma consigliabile per gestione DB più complessa), json. Valutare l'uso di librerie UI aggiuntive per Streamlit, se necessarie, per migliorare l'aspetto e la funzionalità dell'interfaccia.

Considerazioni UI/UX:

User-Friendliness Prioritaria: L'interfaccia deve essere estremamente intuitiva, guidata e facile da usare anche per utenti non tecnici. Testare l'interfaccia con utenti non tecnici per raccogliere feedback e iterare sul design.

Flusso di Lavoro Lineare: Guidare l'utente passo passo attraverso la configurazione del funnel, riducendo la complessità percepita. Utilizzare indicatori di progresso o un sistema di navigazione chiaro (es. tab, sidebar) per evidenziare il flusso di lavoro.

Automazione: Automatizzare il più possibile le operazioni ripetitive e la creazione di record intermedi nel database. Identificare ulteriori aree dove l'automazione può semplificare il flusso di lavoro e ridurre l'intervento manuale.

Feedback Visivo: Utilizzare messaggi di successo, errore, avviso e visualizzazioni chiare per guidare l'utente e fornire feedback immediato. Assicurarsi che i messaggi di errore siano informativi e suggeriscano soluzioni all'utente.

Design Pulito e Intuitivo: Utilizzare un design pulito, ordinato e facile da navigare. Utilizzare expander, tab o sidebar per organizzare le sezioni. Seguire principi di design UI/UX moderni e accessibili. Considerare l'aspetto responsive per l'utilizzo su diversi dispositivi. Mantenere uno stile visivo coerente e professionale. Utilizzare tooltip e help text contestuali in tutta la dashboard per guidare l'utente.

Funzionalità Avanzate (Potenziali Future Enhancements - Oltre MVP):

Drag-and-Drop per Step e Route: Interfaccia drag-and-drop visuale per ordinare gli step del funnel e definire le route in modo grafico. Questo migliorerebbe notevolmente l'intuitività e la velocità di configurazione del funnel.

Anteprima UI Step: Possibilità di visualizzare un'anteprima (semplificata) della UI di uno step mentre viene configurata. L'anteprima potrebbe essere dinamica e aggiornarsi al modificarsi della configurazione.

Validazione Avanzata: Validazione robusta degli input utente (es. URL step univoche, formati JSON corretti, relazioni valide). Implementare validazione lato client e server per garantire l'integrità dei dati. Aggiungere validazione semantica, come il controllo di cicli nelle route del funnel.

Gestione Avanzata CMS Key: Interfaccia più avanzata per la gestione delle CMS Key, magari con suggerimenti o validazione basata su schemi CMS esterni. Integrare la possibilità di caricare o definire schemi CMS per la validazione e l'auto-completamento delle chiavi.

Versioning Funnel: Sistema di versionamento per salvare e ripristinare diverse versioni della configurazione del funnel. Utilizzare un sistema di versionamento robusto (es. Git-like) per tracciare le modifiche e permettere il rollback a versioni precedenti.

Test A/B Funnel: Funzionalità per configurare e gestire test A/B sui funnel. Integrare strumenti per definire varianti di step, sezioni o componenti e per monitorare le performance delle diverse varianti.

Import/Export Configurazione: Funzionalità per esportare e importare la configurazione di un funnel (JSON o altro formato). Permettere l'esportazione e l'importazione di configurazioni complete o parziali, per facilitare la condivisione e il backup.

Gestione Utenti e Permessi: (Se necessario) Sistema di autenticazione e autorizzazione per gestire utenti e permessi di accesso alla dashboard. Implementare un sistema di autenticazione sicuro e un modello di autorizzazione granulare per controllare l'accesso alle funzionalità e ai dati. Considerare l'integrazione con sistemi di autenticazione esistenti (es. OAuth 2.0, LDAP).

Deployment e Scalabilità:

Considerare fin da subito le opzioni di deployment (es. Streamlit Community Cloud, server dedicato, containerizzazione con Docker). Scegliere una strategia di deployment adatta al carico previsto e alle esigenze di sicurezza e affidabilità. Documentare chiaramente il processo di deployment.

Progettare l'applicazione pensando alla potenziale scalabilità futura (anche se per un MVP iniziale la scalabilità potrebbe non essere la priorità). Utilizzare architetture scalabili e pattern di progettazione che facilitino l'espansione futura dell'applicazione.

Testing e Documentazione:

Implementare test unitari e test di integrazione per garantire la qualità e la stabilità dell'applicazione. Utilizzare un framework di testing robusto (es. pytest) e mirare a una copertura di test elevata. Implementare test automatici per la UI (test di regressione visiva).

Documentare il codice e creare una guida utente per la dashboard. Creare una documentazione tecnica dettagliata del codice (API documentation, architettura). Sviluppare una guida utente completa e facile da consultare, con tutorial, esempi e FAQ. Integrare help test contestuali e walkthrough interattivi direttamente nella dashboard.

Metriche di Successo:

Riduzione del tempo necessario per creare e configurare un funnel. Misurare il tempo medio di creazione di un funnel prima e dopo l'introduzione della dashboard.

Aumento dell'autonomia degli utenti non tecnici nella gestione dei funnel. Valutare tramite sondaggi o interviste il livello di autonomia percepito dagli utenti non tecnici.

Diminuzione degli errori nella configurazione dei funnel. Monitorare gli errori di configurazione segnalati dagli utenti o rilevati dal sistema di validazione. Misurare la frequenza di errori prima e dopo l'introduzione della dashboard.

Feedback positivo degli utenti sull'usabilità e l'intuitività della dashboard. Raccogliere feedback degli utenti tramite sondaggi, interviste e canali di feedback integrati nella dashboard. Utilizzare metriche di usabilità standard (es. System Usability Scale - SUS). Monitorare il Net Promoter Score (NPS) per valutare la soddisfazione degli utenti.

Tono e Stile del Progetto:

Il progetto deve essere sviluppato con un approccio pragmatico e orientato alla soluzione. L'enfasi deve essere sulla semplicità d'uso e sull'efficacia nel raggiungere l'obiettivo di creare una dashboard funnel manager "a prova di stupido". L'eleganza del codice e le funzionalità avanzate sono secondarie rispetto alla user-friendliness per la versione MVP. Mantenere un approccio iterativo e agile, con cicli di sviluppo brevi e feedback frequenti degli utenti. Priorizzare la qualità del codice e la manutenibilità per garantire la sostenibilità del progetto nel tempo. Adottare un approccio "mobile-first" nel design dell'interfaccia, garantendo un'esperienza utente ottimale anche su dispositivi mobili.

Schema del database:

-- product.products definition

-- Drop table

-- DROP TABLE product.products;

CREATE TABLE product.products (
id serial4 NOT NULL,
product_code varchar NOT NULL,
product_description varchar NULL,
start_date date NULL,
end_date date NULL,
recurring bool DEFAULT false NOT NULL,
external_id varchar NULL,
insurance_premium numeric(10, 4) NULL,
insurance_company varchar NULL,
insurance_company_logo varchar NULL,
business varchar NULL,
title_prod varchar NULL,
short_description varchar NULL,
description varchar NULL,
conditions varchar NULL,
information_package varchar NULL,
conditions_package varchar NULL,
display_price varchar NULL,
price numeric(10, 4) NULL,
only_contractor bool NULL,
maximum_insurable numeric NULL,
can_open_claim bool NULL,
holder_maximum_age numeric NULL,
holder_minimum_age numeric NULL,
show_in_dashboard bool NULL,
product_image_id int4 NOT NULL,
catalog_id int4 NULL,
properties jsonb NULL,
quotator_type varchar NULL,
show_addons_in_shopping_cart bool NULL,
thumbnail bool NULL,
privacy_documentation_link varchar NULL,
informative_set varchar NULL,
attachment_3_4 varchar NULL,
extras jsonb NULL,
plan_id varchar NULL,
plan_name varchar NULL,
duration int4 NULL,
product_type varchar NULL,
legacy jsonb NULL,
duration_type varchar NULL,
medium_tax_ratio float8 NULL,
ia_code varchar NULL,
ia_net_commission float8 NULL,
CONSTRAINT products_pkey PRIMARY KEY (id),
CONSTRAINT uk_products UNIQUE (product_code)
);

-- product.products foreign keys

ALTER TABLE product.products ADD CONSTRAINT products_product_image_id_fkey FOREIGN KEY (product_image_id) REFERENCES product.product_images(id);
-- Drop table

-- DROP TABLE funnel_manager."condition";

CREATE TABLE funnel_manager."condition" (
id serial4 NOT NULL,
"data" jsonb NULL,
CONSTRAINT condition_pkey PRIMARY KEY (id)
);

-- funnel_manager.step definition

-- Drop table

-- DROP TABLE funnel_manager.step;

CREATE TABLE funnel_manager.step (
id serial4 NOT NULL,
step_url varchar(255) NOT NULL,
shopping_cart jsonb NULL,
post_message bool DEFAULT false NULL,
step_code varchar NULL,
gtm_reference jsonb NULL,
CONSTRAINT step_pkey PRIMARY KEY (id),
CONSTRAINT step_type_uq UNIQUE (step_url)
);

-- funnel_manager.workflow definition

-- Drop table

-- DROP TABLE funnel_manager.workflow;

CREATE TABLE funnel_manager.workflow (
id serial4 NOT NULL,
description varchar(255) NULL,
CONSTRAINT workflow_pk PRIMARY KEY (id)
);

-- funnel_manager.funnel definition

-- Drop table

-- DROP TABLE funnel_manager.funnel;

CREATE TABLE funnel_manager.funnel (
id bigserial NOT NULL,
workflow_id int8 NULL,
broker_id int8 NULL,
"name" varchar(255) NULL,
funnel_process int8 NULL,
"type" varchar(255) NULL,
product_id int8 NULL,
CONSTRAINT funnel_name_uq UNIQUE (name),
CONSTRAINT funnel_pkey PRIMARY KEY (id),
CONSTRAINT workflow_fk FOREIGN KEY (workflow_id) REFERENCES funnel_manager.workflow(id)
);

-- funnel_manager.order_funnel definition

-- Drop table

-- DROP TABLE funnel_manager.order_funnel;

CREATE TABLE funnel_manager.order_funnel (
id serial4 NOT NULL,
order_id varchar(255) NULL,
funnel_id int8 NULL,
previous_steps jsonb NULL,
next_step int8 NULL,
CONSTRAINT order_funnel_pkey PRIMARY KEY (id),
CONSTRAINT orderid_uq UNIQUE (order_id),
CONSTRAINT funnel_fk FOREIGN KEY (funnel_id) REFERENCES funnel_manager.funnel(id),
CONSTRAINT next_step_fk FOREIGN KEY (next_step) REFERENCES funnel_manager.step(id)
);

-- funnel_manager.route definition

-- Drop table

-- DROP TABLE funnel_manager.route;

CREATE TABLE funnel_manager.route (
id serial4 NOT NULL,
nextstep_id int8 NULL,
fromstep_id int8 NULL,
workflow_id int8 NULL,
route_config jsonb NULL,
CONSTRAINT transition_pkey PRIMARY KEY (id),
CONSTRAINT from_step_fkey FOREIGN KEY (fromstep_id) REFERENCES funnel_manager.step(id),
CONSTRAINT next_step_fkey FOREIGN KEY (nextstep_id) REFERENCES funnel_manager.step(id),
CONSTRAINT workflow_fkey FOREIGN KEY (workflow_id) REFERENCES funnel_manager.workflow(id)
);

-- funnel_manager.route_condition definition

-- Drop table

-- DROP TABLE funnel_manager.route_condition;

CREATE TABLE funnel_manager.route_condition (
id serial4 NOT NULL,
route_id int8 NULL,
condition_id int8 NULL,
broker_id int8 NULL,
product_id int8 NULL,
CONSTRAINT route_condition_pkey PRIMARY KEY (id),
CONSTRAINT condition_fkey FOREIGN KEY (condition_id) REFERENCES funnel_manager."condition"(id),
CONSTRAINT route_fkey FOREIGN KEY (route_id) REFERENCES funnel_manager.route(id)
);

-- Drop table

-- DROP TABLE design.component;

CREATE TABLE design.component (
id int8 DEFAULT nextval('design.hibernate_sequence_component'::regclass) NOT NULL,
component_type varchar NOT NULL,
CONSTRAINT component_pk PRIMARY KEY (id)
);

-- design."section" definition

-- Drop table

-- DROP TABLE design."section";

CREATE TABLE design."section" (
id int8 DEFAULT nextval('design.hibernate_sequence_section'::regclass) NOT NULL,
sectiontype varchar NOT NULL,
CONSTRAINT section_pk PRIMARY KEY (id)
);

-- design."structure" definition

-- Drop table

-- DROP TABLE design."structure";

CREATE TABLE design."structure" (
id int8 DEFAULT nextval('design.hibernate_sequence_structure'::regclass) NOT NULL,
"data" json NOT NULL,
CONSTRAINT structure_pk PRIMARY KEY (id)
);

-- design.component_section definition

-- Drop table

-- DROP TABLE design.component_section;

CREATE TABLE design.component_section (
id int8 DEFAULT nextval('design.hibernate_sequence_component_section'::regclass) NOT NULL,
componentid int8 NOT NULL,
sectionid int8 NOT NULL,
"order" int4 NOT NULL,
key_cms varchar NULL,
CONSTRAINT component_section_pk PRIMARY KEY (id),
CONSTRAINT component_section_componentid_fkey FOREIGN KEY (componentid) REFERENCES design.component(id),
CONSTRAINT component_section_sectionid_fkey FOREIGN KEY (sectionid) REFERENCES design."section"(id)
);

-- design.step_section definition

-- Drop table

-- DROP TABLE design.step_section;

CREATE TABLE design.step_section (
id int8 DEFAULT nextval('design.hibernate_sequence_step_section'::regclass) NOT NULL,
"order" int4 NOT NULL,
sectionid int8 NOT NULL,
stepid int4 NOT NULL,
productid int4 NULL,
brokerid int4 NULL,
orderfieldsstepschema json NULL,
authorized bool DEFAULT false NULL,
CONSTRAINT order_section_pk PRIMARY KEY (id),
CONSTRAINT unique_order_step_product_broker UNIQUE ("order", stepid, productid, brokerid),
CONSTRAINT step_section_sectionid_fkey FOREIGN KEY (sectionid) REFERENCES design."section"(id)
);

-- design.structure_component_section definition

-- Drop table

-- DROP TABLE design.structure_component_section;

CREATE TABLE design.structure_component_section (
id int8 DEFAULT nextval('design.hibernate_sequence_structure_component_section'::regclass) NOT NULL,
component_sectionid int8 NOT NULL,
structureid int8 NOT NULL,
"order" int4 NOT NULL,
CONSTRAINT structure_component_pk PRIMARY KEY (id),
CONSTRAINT structure_component_section_component_sectionid_fkey FOREIGN KEY (component_sectionid) REFERENCES design.component_section(id),
CONSTRAINT structure_component_section_structureid_fkey FOREIGN KEY (structureid) REFERENCES design."structure"(id)
);

-- design.cms_key definition

-- Drop table

-- DROP TABLE design.cms_key;

CREATE TABLE design.cms_key (
id int8 DEFAULT nextval('design.hibernate_sequence_cms'::regclass) NOT NULL,
value json NOT NULL,
structurecomponentsectionid int8 NOT NULL,
CONSTRAINT cms_pk PRIMARY KEY (id),
CONSTRAINT cms_key_structurecomponentsectionid_fkey FOREIGN KEY (structurecomponentsectionid) REFERENCES design.structure_component_section(id)
);