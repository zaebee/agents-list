--
-- PostgreSQL database dump
--

\restrict onrl3GpjFNXcFEHqMbw9DS8rag70vIvCMaBPLSwKDXcJzxuyar6KIXQnGbc0wTW

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: accountstatus; Type: TYPE; Schema: public; Owner: aicrm_user
--

CREATE TYPE public.accountstatus AS ENUM (
    'ACTIVE',
    'SUSPENDED',
    'DELETED',
    'PENDING_VERIFICATION'
);


ALTER TYPE public.accountstatus OWNER TO aicrm_user;

--
-- Name: subscriptiontier; Type: TYPE; Schema: public; Owner: aicrm_user
--

CREATE TYPE public.subscriptiontier AS ENUM (
    'FREE',
    'PRO',
    'ENTERPRISE'
);


ALTER TYPE public.subscriptiontier OWNER TO aicrm_user;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: aicrm_user
--

CREATE TYPE public.userrole AS ENUM (
    'USER',
    'MANAGER',
    'ADMIN'
);


ALTER TYPE public.userrole OWNER TO aicrm_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: aicrm_user
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    event_type character varying(50) NOT NULL,
    resource character varying(100),
    action character varying(50),
    result character varying(20) NOT NULL,
    ip_address character varying(45),
    user_agent text,
    request_id character varying(255),
    details text,
    risk_score integer,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.audit_logs OWNER TO aicrm_user;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: aicrm_user
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_logs_id_seq OWNER TO aicrm_user;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aicrm_user
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: auth_sessions; Type: TABLE; Schema: public; Owner: aicrm_user
--

CREATE TABLE public.auth_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    refresh_token character varying(255) NOT NULL,
    access_token_jti character varying(255) NOT NULL,
    ip_address character varying(45),
    user_agent text,
    device_fingerprint character varying(255),
    is_active boolean,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    last_used timestamp with time zone DEFAULT now()
);


ALTER TABLE public.auth_sessions OWNER TO aicrm_user;

--
-- Name: auth_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: aicrm_user
--

CREATE SEQUENCE public.auth_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_sessions_id_seq OWNER TO aicrm_user;

--
-- Name: auth_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aicrm_user
--

ALTER SEQUENCE public.auth_sessions_id_seq OWNED BY public.auth_sessions.id;


--
-- Name: rate_limit_rules; Type: TABLE; Schema: public; Owner: aicrm_user
--

CREATE TABLE public.rate_limit_rules (
    id integer NOT NULL,
    endpoint_pattern character varying(200) NOT NULL,
    subscription_tier public.subscriptiontier NOT NULL,
    requests_per_minute integer,
    requests_per_hour integer,
    requests_per_day integer,
    burst_size integer,
    created_at timestamp with time zone DEFAULT now(),
    is_active boolean
);


ALTER TABLE public.rate_limit_rules OWNER TO aicrm_user;

--
-- Name: rate_limit_rules_id_seq; Type: SEQUENCE; Schema: public; Owner: aicrm_user
--

CREATE SEQUENCE public.rate_limit_rules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.rate_limit_rules_id_seq OWNER TO aicrm_user;

--
-- Name: rate_limit_rules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aicrm_user
--

ALTER SEQUENCE public.rate_limit_rules_id_seq OWNED BY public.rate_limit_rules.id;


--
-- Name: subscription_features; Type: TABLE; Schema: public; Owner: aicrm_user
--

CREATE TABLE public.subscription_features (
    id integer NOT NULL,
    feature_name character varying(100) NOT NULL,
    description text,
    free_tier boolean,
    pro_tier boolean,
    enterprise_tier boolean,
    free_limit integer,
    pro_limit integer,
    enterprise_limit integer,
    created_at timestamp with time zone DEFAULT now(),
    is_active boolean
);


ALTER TABLE public.subscription_features OWNER TO aicrm_user;

--
-- Name: subscription_features_id_seq; Type: SEQUENCE; Schema: public; Owner: aicrm_user
--

CREATE SEQUENCE public.subscription_features_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.subscription_features_id_seq OWNER TO aicrm_user;

--
-- Name: subscription_features_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aicrm_user
--

ALTER SEQUENCE public.subscription_features_id_seq OWNED BY public.subscription_features.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: aicrm_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(50) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(100),
    is_active boolean,
    is_verified boolean,
    account_status public.accountstatus,
    role public.userrole,
    subscription_tier public.subscriptiontier,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_login timestamp with time zone,
    email_verification_token character varying(255),
    password_reset_token character varying(255),
    password_reset_expires timestamp with time zone,
    monthly_tasks_created integer,
    last_task_reset timestamp with time zone DEFAULT now()
);


ALTER TABLE public.users OWNER TO aicrm_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: aicrm_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO aicrm_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aicrm_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: auth_sessions id; Type: DEFAULT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.auth_sessions ALTER COLUMN id SET DEFAULT nextval('public.auth_sessions_id_seq'::regclass);


--
-- Name: rate_limit_rules id; Type: DEFAULT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.rate_limit_rules ALTER COLUMN id SET DEFAULT nextval('public.rate_limit_rules_id_seq'::regclass);


--
-- Name: subscription_features id; Type: DEFAULT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.subscription_features ALTER COLUMN id SET DEFAULT nextval('public.subscription_features_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: aicrm_user
--

COPY public.audit_logs (id, user_id, event_type, resource, action, result, ip_address, user_agent, request_id, details, risk_score, created_at) FROM stdin;
\.


--
-- Data for Name: auth_sessions; Type: TABLE DATA; Schema: public; Owner: aicrm_user
--

COPY public.auth_sessions (id, user_id, refresh_token, access_token_jti, ip_address, user_agent, device_fingerprint, is_active, expires_at, created_at, last_used) FROM stdin;
\.


--
-- Data for Name: rate_limit_rules; Type: TABLE DATA; Schema: public; Owner: aicrm_user
--

COPY public.rate_limit_rules (id, endpoint_pattern, subscription_tier, requests_per_minute, requests_per_hour, requests_per_day, burst_size, created_at, is_active) FROM stdin;
1	/api/command.*	FREE	5	50	200	10	2025-08-15 18:19:51.398076+00	t
2	/api/command.*	PRO	30	500	5000	10	2025-08-15 18:19:51.398076+00	t
3	/api/command.*	ENTERPRISE	100	2000	20000	10	2025-08-15 18:19:51.398076+00	t
\.


--
-- Data for Name: subscription_features; Type: TABLE DATA; Schema: public; Owner: aicrm_user
--

COPY public.subscription_features (id, feature_name, description, free_tier, pro_tier, enterprise_tier, free_limit, pro_limit, enterprise_limit, created_at, is_active) FROM stdin;
1	command_execution	Execute natural language commands	t	t	t	10	\N	\N	2025-08-15 18:19:51.398076+00	t
2	ai_agent_access	Access to AI agents for task assistance	t	t	t	9	46	\N	2025-08-15 18:19:51.398076+00	t
3	analytics_dashboard	Access to analytics and reporting	f	t	t	\N	\N	\N	2025-08-15 18:19:51.398076+00	t
4	api_access	REST API access	f	t	t	\N	\N	\N	2025-08-15 18:19:51.398076+00	t
5	billing_dashboard	Access to billing and subscription management	f	t	t	\N	\N	\N	2025-08-15 18:19:51.398076+00	t
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: aicrm_user
--

COPY public.users (id, email, username, hashed_password, full_name, is_active, is_verified, account_status, role, subscription_tier, created_at, updated_at, last_login, email_verification_token, password_reset_token, password_reset_expires, monthly_tasks_created, last_task_reset) FROM stdin;
1	user@example.com	admin	$argon2id$v=19$m=65536,t=3,p=1$1bq31ro3ZqyVUiolZMy51w$kOSqD4l5a/Cc0a8n1GNPSZ+wLkiiuf073AY0VBxMMoU	string	t	f	PENDING_VERIFICATION	USER	FREE	2025-08-15 18:23:39.854274+00	2025-08-15 18:23:39.854274+00	\N	fIP6j1eYxSNeuEuNHI_zvaN0vfhLlvwUfat9cWYVBLI	\N	\N	0	2025-08-15 18:23:39.854274+00
\.


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aicrm_user
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 1, false);


--
-- Name: auth_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aicrm_user
--

SELECT pg_catalog.setval('public.auth_sessions_id_seq', 1, false);


--
-- Name: rate_limit_rules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aicrm_user
--

SELECT pg_catalog.setval('public.rate_limit_rules_id_seq', 3, true);


--
-- Name: subscription_features_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aicrm_user
--

SELECT pg_catalog.setval('public.subscription_features_id_seq', 5, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aicrm_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: auth_sessions auth_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_pkey PRIMARY KEY (id);


--
-- Name: rate_limit_rules rate_limit_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.rate_limit_rules
    ADD CONSTRAINT rate_limit_rules_pkey PRIMARY KEY (id);


--
-- Name: subscription_features subscription_features_pkey; Type: CONSTRAINT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.subscription_features
    ADD CONSTRAINT subscription_features_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_audit_logs_event_type; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE INDEX ix_audit_logs_event_type ON public.audit_logs USING btree (event_type);


--
-- Name: ix_audit_logs_id; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE INDEX ix_audit_logs_id ON public.audit_logs USING btree (id);


--
-- Name: ix_auth_sessions_access_token_jti; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE INDEX ix_auth_sessions_access_token_jti ON public.auth_sessions USING btree (access_token_jti);


--
-- Name: ix_auth_sessions_id; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE INDEX ix_auth_sessions_id ON public.auth_sessions USING btree (id);


--
-- Name: ix_auth_sessions_refresh_token; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE UNIQUE INDEX ix_auth_sessions_refresh_token ON public.auth_sessions USING btree (refresh_token);


--
-- Name: ix_rate_limit_rules_endpoint_pattern; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE INDEX ix_rate_limit_rules_endpoint_pattern ON public.rate_limit_rules USING btree (endpoint_pattern);


--
-- Name: ix_rate_limit_rules_id; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE INDEX ix_rate_limit_rules_id ON public.rate_limit_rules USING btree (id);


--
-- Name: ix_subscription_features_feature_name; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE UNIQUE INDEX ix_subscription_features_feature_name ON public.subscription_features USING btree (feature_name);


--
-- Name: ix_subscription_features_id; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE INDEX ix_subscription_features_id ON public.subscription_features USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: aicrm_user
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: auth_sessions auth_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aicrm_user
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict onrl3GpjFNXcFEHqMbw9DS8rag70vIvCMaBPLSwKDXcJzxuyar6KIXQnGbc0wTW

