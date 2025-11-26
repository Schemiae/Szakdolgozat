--
-- PostgreSQL database dump
--

\restrict xKdGJeFckefBPyK72otge4Jh7YvxKLRNDCgWC8gap65vajtbcE4xsmxBlSmp0Vw

-- Dumped from database version 14.19 (Ubuntu 14.19-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.19 (Ubuntu 14.19-0ubuntu0.22.04.1)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bus; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bus (
    plate character varying(20) NOT NULL,
    type character varying(50),
    km integer,
    year integer,
    garage integer,
    description text,
    status character varying(20),
    line character varying(20),
    owner character varying,
    favourite boolean DEFAULT false NOT NULL
);


ALTER TABLE public.bus OWNER TO postgres;

--
-- Name: garages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.garages (
    id integer NOT NULL,
    name character varying(50),
    location character varying(100)
);


ALTER TABLE public.garages OWNER TO postgres;

--
-- Name: garazs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.garazs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.garazs_id_seq OWNER TO postgres;

--
-- Name: garazs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.garazs_id_seq OWNED BY public.garages.id;


--
-- Name: issues; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.issues (
    id integer NOT NULL,
    bus character varying(20),
    "time" character varying,
    repair_time interval,
    repair_cost integer,
    description text
);


ALTER TABLE public.issues OWNER TO postgres;

--
-- Name: lines; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.lines (
    name character varying NOT NULL,
    provider_garage_id integer,
    travel_time_garage integer,
    travel_time_line integer NOT NULL
);


ALTER TABLE public.lines OWNER TO postgres;

--
-- Name: market_listings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.market_listings (
    id integer NOT NULL,
    bus_plate character varying(32) NOT NULL,
    seller_username character varying(64) NOT NULL,
    price integer NOT NULL,
    status character varying(16) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    sold_at timestamp without time zone,
    CONSTRAINT market_listings_price_check CHECK ((price >= 0))
);


ALTER TABLE public.market_listings OWNER TO postgres;

--
-- Name: market_listings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.market_listings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.market_listings_id_seq OWNER TO postgres;

--
-- Name: market_listings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.market_listings_id_seq OWNED BY public.market_listings.id;


--
-- Name: muszaki_hiba_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.muszaki_hiba_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.muszaki_hiba_id_seq OWNER TO postgres;

--
-- Name: muszaki_hiba_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.muszaki_hiba_id_seq OWNED BY public.issues.id;


--
-- Name: schedule_assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.schedule_assignments (
    schedule_id integer NOT NULL,
    block_idx integer NOT NULL,
    bus_plate character varying
);


ALTER TABLE public.schedule_assignments OWNER TO postgres;

--
-- Name: schedules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.schedules (
    id integer NOT NULL,
    username character varying,
    line_name character varying,
    garage_id integer,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL,
    frequency integer NOT NULL,
    bid_price integer DEFAULT 0,
    status text DEFAULT 'pending'::text,
    frame text,
    CONSTRAINT schedules_frame_check CHECK ((frame = ANY (ARRAY['morning'::text, 'midday'::text, 'afternoon'::text, 'evening'::text, 'night'::text])))
);


ALTER TABLE public.schedules OWNER TO postgres;

--
-- Name: schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.schedules_id_seq OWNER TO postgres;

--
-- Name: schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.schedules_id_seq OWNED BY public.schedules.id;


--
-- Name: user_garages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_garages (
    username character varying NOT NULL,
    garage_id integer NOT NULL
);


ALTER TABLE public.user_garages OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    username character varying NOT NULL,
    password character varying NOT NULL,
    balance integer DEFAULT 50000 NOT NULL,
    is_admin boolean
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: garages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.garages ALTER COLUMN id SET DEFAULT nextval('public.garazs_id_seq'::regclass);


--
-- Name: issues id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issues ALTER COLUMN id SET DEFAULT nextval('public.muszaki_hiba_id_seq'::regclass);


--
-- Name: market_listings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_listings ALTER COLUMN id SET DEFAULT nextval('public.market_listings_id_seq'::regclass);


--
-- Name: schedules id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedules ALTER COLUMN id SET DEFAULT nextval('public.schedules_id_seq'::regclass);


--
-- Data for Name: bus; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bus (plate, type, km, year, garage, description, status, line, owner, favourite) FROM stdin;
ASD-002	Volvo 7700	0	2004	2	sda	Service	-	testuser2	f
NGC-149	Mercedes Citaro	2001340	2006	2	Og hangzavar	menetrend	7E	testuser	f
MUT-981	VanHool AG 300	1610293	2001	2	MUTAA	menetrend	7E	testuser2	f
PCC-934	Mercedes Citaro	80280	2006	2	Isten Nyila	menetrend	7E	testuser2	f
SSH-222	VanHool AG300	4240	2002	1	ssh 3	menetrend	106	testuser	f
SWF-652	Mercedes Conecto	966370	2007	1	Sárga cuccok	menetrend	106	testuser	f
FLA-420	Mercedes Sprinter	3630	2003	2	Nem megbízható :) :)	Service	-	\N	t
PKD-001	Ikarus 196V szóló	0	2001	1	Fincsi	KT	-	\N	f
MUT-988	VanHool AG300	200	2002	2	YESSS	KT	-	\N	f
RTA-297	Mercedes Citaro	70470	2003	2	Legjobb kocsi	KT	-	\N	t
HPH-128	Volvo 7700	6090	2004	2	Nagyba	KT	-	\N	t
BPI-759	Ikarus 280	3004240	1978	1	Bajos	menetrend	106	testuser	f
BPO-657	Modulo M108d	200	2008	2	Régi darab	KT	-	\N	f
FLR-701	Volvo 7700	124070	2002	1	Laptop reklám	KT	-	testuser	f
SIF-013	Mercedes Citaro	1228650	2005	2	Leér a csuklója	KT	-	\N	t
SVA-793	Modulo m108d	610440	2009	2	Pattogó	Service	-	\N	f
PMP-914	Modulo M108d	0	2008	1	:)	KT	-	testuser	f
LOV-881	VanHool AG300	2222922	1991	2	Kocka	Service	-	testuser	t
\.


--
-- Data for Name: garages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.garages (id, name, location) FROM stdin;
1	Kelenföldi Garázs	Budapest XI.
2	Óbudai Garázs	Budapest III.
3	Cinkotai Autóbuszgarázs	Budapest XVI.
\.


--
-- Data for Name: issues; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.issues (id, bus, "time", repair_time, repair_cost, description) FROM stdin;
27	FLA-420	2025.10.24 - 22:22:25	00:00:01	5000000	sad
29	LOV-881	2025.11.03 - 19:55:58	00:00:23	412	hhh
30	ASD-002	2025.11.08 - 17:32:25	00:00:00	1000	ijj
36	SVA-793	2025.11.23 - 16:20:54	00:00:00	100	test
\.


--
-- Data for Name: lines; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.lines (name, provider_garage_id, travel_time_garage, travel_time_line) FROM stdin;
106	1	20	30
7E	2	15	15
9	2	5	50
\.


--
-- Data for Name: market_listings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.market_listings (id, bus_plate, seller_username, price, status, created_at, sold_at) FROM stdin;
4	SWF-652	testuser	10000	sold	2025-10-19 16:28:43.957898	2025-10-19 14:29:26.601018
6	BPI-759	testuser	300000	canceled	2025-10-19 16:40:37.960886	\N
9	FLR-701	testuser	10000	sold	2025-10-24 14:06:26.144738	2025-10-24 12:06:46.851003
11	FLR-701	testuser	10000	sold	2025-10-24 14:10:35.681944	2025-10-24 12:30:35.053519
14	BPI-759	testuser	500000	canceled	2025-11-03 18:16:16.47835	\N
16	MUT-981	testuser2	600000	canceled	2025-11-08 17:27:22.543989	\N
17	MUT-981	testuser2	40000000	canceled	2025-11-08 17:27:49.607595	\N
18	MUT-981	testuser2	10000001	canceled	2025-11-08 17:28:16.352003	\N
20	ASD-002	testuser	10000	sold	2025-11-08 17:30:47.970902	2025-11-08 16:31:08.890577
19	PCC-934	testuser	10000	sold	2025-11-08 17:30:37.791046	2025-11-08 16:32:02.688413
21	ASD-002	testuser2	10000	active	2025-11-08 17:32:49.597729	\N
15	FLR-701	testuser	60000	sold	2025-11-03 18:25:56.015522	2025-11-09 20:07:32.11736
\.


--
-- Data for Name: schedule_assignments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.schedule_assignments (schedule_id, block_idx, bus_plate) FROM stdin;
59	0	BPI-759
59	1	SSH-222
59	2	SWF-652
66	0	FLR-701
66	1	NGC-149
67	0	MUT-981
67	1	PCC-934
\.


--
-- Data for Name: schedules; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.schedules (id, username, line_name, garage_id, start_time, end_time, frequency, bid_price, status, frame) FROM stdin;
67	testuser2	7E	2	20:00:00	24:00:00	40	14422	active	night
66	testuser	7E	2	16:00:00	20:00:00	40	15000	active	evening
59	testuser	106	1	20:00:00	24:00:00	30	15000	active	night
\.


--
-- Data for Name: user_garages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_garages (username, garage_id) FROM stdin;
testuser	1
testuser	3
testuser	2
testuser2	2
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (username, password, balance, is_admin) FROM stdin;
testuser2	$2b$12$hVfrIR8m39nOz.VFW0gO1O6iR2ph65sCkeSAHxeg82WalfnunawZm	36828	f
testuser	$2b$12$2AhE6CPntzhppD3oE1dJ4uU1tJvvt4.WR03EKiQ5MH4dAe0eOtq/e	121016	f
testuser3	$2b$12$MPwBu3Dq6MQV.b34AYjMZuZk.vf6Z5nMD41lhLLAhyPaNjFOJxelC	50000	f
\.


--
-- Name: garazs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.garazs_id_seq', 3, true);


--
-- Name: market_listings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.market_listings_id_seq', 25, true);


--
-- Name: muszaki_hiba_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.muszaki_hiba_id_seq', 36, true);


--
-- Name: schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.schedules_id_seq', 70, true);


--
-- Name: bus busz_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bus
    ADD CONSTRAINT busz_pkey PRIMARY KEY (plate);


--
-- Name: garages garazs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.garages
    ADD CONSTRAINT garazs_pkey PRIMARY KEY (id);


--
-- Name: lines lines_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lines
    ADD CONSTRAINT lines_pkey PRIMARY KEY (name);


--
-- Name: market_listings market_listings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_listings
    ADD CONSTRAINT market_listings_pkey PRIMARY KEY (id);


--
-- Name: issues muszaki_hiba_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issues
    ADD CONSTRAINT muszaki_hiba_pkey PRIMARY KEY (id);


--
-- Name: schedule_assignments schedule_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedule_assignments
    ADD CONSTRAINT schedule_assignments_pkey PRIMARY KEY (schedule_id, block_idx);


--
-- Name: schedules schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_pkey PRIMARY KEY (id);


--
-- Name: user_garages user_garages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_garages
    ADD CONSTRAINT user_garages_pkey PRIMARY KEY (username, garage_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (username);


--
-- Name: uq_listing_active_bus; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_listing_active_bus ON public.market_listings USING btree (bus_plate) WHERE ((status)::text = 'active'::text);


--
-- Name: bus busz_garazs_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bus
    ADD CONSTRAINT busz_garazs_fkey FOREIGN KEY (garage) REFERENCES public.garages(id);


--
-- Name: lines lines_provider_garage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lines
    ADD CONSTRAINT lines_provider_garage_id_fkey FOREIGN KEY (provider_garage_id) REFERENCES public.garages(id);


--
-- Name: market_listings market_listings_bus_rendszam_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_listings
    ADD CONSTRAINT market_listings_bus_rendszam_fkey FOREIGN KEY (bus_plate) REFERENCES public.bus(plate) ON DELETE CASCADE;


--
-- Name: market_listings market_listings_seller_username_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_listings
    ADD CONSTRAINT market_listings_seller_username_fkey FOREIGN KEY (seller_username) REFERENCES public.users(username) ON DELETE CASCADE;


--
-- Name: issues muszaki_hiba_busz_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issues
    ADD CONSTRAINT muszaki_hiba_busz_fkey FOREIGN KEY (bus) REFERENCES public.bus(plate);


--
-- Name: bus owner_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bus
    ADD CONSTRAINT owner_user_fkey FOREIGN KEY (owner) REFERENCES public.users(username) MATCH FULL;


--
-- Name: schedules schedules_garage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_garage_id_fkey FOREIGN KEY (garage_id) REFERENCES public.garages(id);


--
-- Name: schedules schedules_line_name_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_line_name_fkey FOREIGN KEY (line_name) REFERENCES public.lines(name);


--
-- Name: schedules schedules_username_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_username_fkey FOREIGN KEY (username) REFERENCES public.users(username);


--
-- Name: user_garages user_garages_garage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_garages
    ADD CONSTRAINT user_garages_garage_id_fkey FOREIGN KEY (garage_id) REFERENCES public.garages(id);


--
-- Name: user_garages user_garages_username_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_garages
    ADD CONSTRAINT user_garages_username_fkey FOREIGN KEY (username) REFERENCES public.users(username);


--
-- PostgreSQL database dump complete
--

\unrestrict xKdGJeFckefBPyK72otge4Jh7YvxKLRNDCgWC8gap65vajtbcE4xsmxBlSmp0Vw

