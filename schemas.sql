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