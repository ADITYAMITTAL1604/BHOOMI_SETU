**BHOOMISETU**

**SIH26016 — Real-Time National Land Acquisition & Management System**

**DATA STRATEGY & DATASET PLAYBOOK**

| Core strategyUse real public government/geospatial data to establish authenticity and context, while using realistic synthetic parcel-level, workflow, compensation, R\&R and historical event data to power the prototype and predictive analytics. |
| :---- |

# **1\. Executive Summary**

For a 4–5 day SIH prototype, BhoomiSetu does not need confidential owner-level land data or a complete national production dataset. The strongest approach is a hybrid evidence model: real public datasets for geography, programme context and schema; synthetic operational data for parcel-level workflow, lifecycle history and predictive modelling.

This approach lets the team demonstrate a realistic national land-acquisition command system without pretending that fabricated records are official government data.

| Data family | Recommended source | Use in BhoomiSetu | Prototype status |
| :---- | :---- | :---- | :---- |
| Administrative boundaries | Survey of India | State/district/tehsil/village hierarchy; GIS base | Real |
| Land-data readiness | DILRMP MIS | National/state context and digitisation readiness indicators | Real |
| Acquisition schema / project metrics | LACRRIS | Real field structure; project-level benchmarks where publicly available | Real / partial |
| Geospatial context | Bhuvan / NRSC | Satellite/context layers where permitted | Real / licensed |
| Infrastructure context | OpenStreetMap | Road/rail/corridor context | Real |
| Public acquisition documents | Government portals / India Code | Notification/SIA/document examples | Real |
| Parcel lifecycle | Synthetic generator | Acquisition stages, events, status, bottlenecks | Mock |
| Compensation / R\&R | Synthetic generator | Payment, affected families, rehabilitation states | Mock |
| Historical snapshots | Synthetic generator | Training/evaluation for delay-risk model | Mock |
| Officer/workload / SLA | Synthetic generator | Operational bottleneck simulation | Mock |

# **2\. Real Data Sources to Use**

## **2.1 LACRRIS — Land Acquisition, Compensation, Rehabilitation & Resettlement Information System**

LACRRIS is the most important real-world reference for BhoomiSetu because it sits directly inside the Department of Land Resources land-acquisition ecosystem. Public reporting views expose fields such as project name, land-requiring body, district, rural/urban classification, land extent, stages/notifications, awards, payments, possession, affected families and compensation/R\&R amounts. This gives you the real schema and vocabulary around which the prototype should be designed.

Recommended use: treat LACRRIS as the benchmark for your data model and, where public records are accessible, seed a small set of non-sensitive real project-level records. Do not make the live website a runtime dependency for the hackathon.

project\_id | project\_name | land\_requiring\_body | state | district | rural\_urban  
land\_extent\_ha | SIA\_date | notification\_date | award\_date | payment\_date | possession\_date  
affected\_families | displaced\_families | compensation\_amount | RR\_amount

## **2.2 DILRMP MIS — Digital India Land Records Modernization Programme**

Use DILRMP MIS for national/state-level land-data readiness, digitisation and cadastral-map context. The current MIS provides statistics on computerized land records, digitized maps, map/RoR linkage, geo-referencing and ULPIN-related progress. These metrics are useful for the national command dashboard and for explaining why data readiness varies across jurisdictions.

state | district | villages | computerized\_land\_records | digitized\_maps  
ror\_map\_linked | georeferenced | ulpin\_status

## **2.3 Survey of India — Village Boundary Database**

Use the Survey of India village-boundary data as the geographic skeleton of the demo. This gives you authentic state, district, sub-district and village polygons rather than invented administrative shapes.

* Use real administrative polygons wherever the terms permit your intended hackathon use.  
* Use these boundaries to constrain synthetic parcels and project corridors.  
* Keep the original source attribution with the dataset.

## **2.4 Bhuvan / NRSC — Geospatial Context**

Bhuvan can supply useful satellite and thematic context such as administrative boundaries, land-use/land-cover, soils and related geospatial layers. Use only the layers/services whose current terms permit the intended use, and retain attribution. Do not present Bhuvan content as your own.

## **2.5 OpenStreetMap — Infrastructure Context**

Use OSM for roads, highways, railway lines, settlements and other infrastructure context. It is particularly useful for creating a realistic acquisition corridor and identifying the villages/infrastructure that intersect the project footprint. Do not use OSM as a cadastral ownership source.

## **2.6 Public Government Notifications and Legal Documents**

Public land-acquisition documents can be used to demonstrate document ingestion and structured extraction. Useful document types include preliminary notifications, SIA documents, declarations, award-related notices and R\&R records. The RFCTLARR legal framework provides the formal stages and terminology your workflow should reflect.

# **3\. Data You Should Generate as Mock/Synthetic**

The detailed event history needed for AI prediction will almost certainly be the hardest part to obtain as open, clean, nationwide data. Generate it instead. The key is not randomness: synthetic data must contain realistic relationships that mirror how acquisition delays actually arise.

## **3.1 Parcel-Level Acquisition Records**

parcel\_id, project\_id, state, district, tehsil, village, survey\_number, area\_hectare, geometry, current\_stage, stage\_start\_date, stage\_target\_date, stage\_completion\_date, days\_in\_current\_stage, sla\_days, sla\_breach

## **3.2 Compensation**

parcel\_id, assessed\_amount, approved\_amount, paid\_amount, payment\_date, payment\_status

## **3.3 Rehabilitation & Resettlement**

family\_id, parcel\_id, affected, displaced, R\&R\_eligibility, R\&R\_status, benefit\_type, benefit\_status

## **3.4 Legal / Ownership Disputes**

parcel\_id, dispute\_type, dispute\_status, case\_date, days\_pending, administrative\_impact

## **3.5 Officer / Team Workload**

officer\_id, district, role, assigned\_cases, completed\_cases, pending\_cases, average\_processing\_days, sla\_breaches

## **3.6 Historical Snapshots**

project\_id, snapshot\_date, pending\_parcels, completed\_parcels, average\_stage\_days, sla\_breaches, compensation\_pending, RR\_pending, possession\_pending, processing\_rate

## **3.7 Create Multiple “Project Personalities”**

Do not make every project behave similarly. Create deliberately different scenarios so the AI layer has meaningful patterns to detect and the demo can show contrasting outcomes.

| Scenario | Synthetic pattern | Expected BhoomiSetu output |
| :---- | :---- | :---- |
| Healthy project | Fast processing, few disputes, backlog declining | LOW risk |
| Verification bottleneck | Large ownership-verification backlog, rising SLA breaches | HIGH risk — verification bottleneck |
| Compensation bottleneck | Award completed but payment queue growing | HIGH risk — compensation bottleneck |
| Legal bottleneck | High dispute rate; possession blocked | HIGH risk — legal/ownership bottleneck |
| Capacity bottleneck | Officer workload far above district baseline | HIGH risk — operational capacity issue |

# **4\. How to Generate the Synthetic Dataset**

The recommended generator is Python using Pandas, NumPy, Faker, GeoPandas and Shapely. The generator should start from real administrative geography, create realistic project corridors and parcel geometries, then assign acquisition events and correlated bottlenecks.

REAL ADMIN BOUNDARIES  
        ↓  
Select 3–5 districts / 15–30 villages  
        ↓  
Create synthetic project corridors  
        ↓  
Generate synthetic parcels inside real village polygons  
        ↓  
Assign lifecycle stages and events  
        ↓  
Inject realistic bottlenecks  
        ↓  
Generate historical snapshots  
        ↓  
Generate target labels  
        ↓  
Train \+ test delay-risk model

## **4.1 Generate Realistic Parcel Geometry**

* Preferred: use openly accessible parcel geometry where permitted, then attach synthetic lifecycle attributes.  
* Fallback: generate synthetic parcel polygons inside real village boundaries using spatial subdivision / Voronoi-style partitioning.  
* Avoid random rectangles scattered over a map; judges can immediately spot unrealistic GIS data.

## **4.2 Generate a Realistic Acquisition Corridor**

Select a real road/rail corridor from a permitted geospatial source such as OSM. Buffer the corridor and intersect it with village boundaries and your synthetic parcel layer. This allows BhoomiSetu to genuinely compute which parcels are affected by the project footprint.

project corridor → buffer → village intersection → parcel intersection → affected parcel set

## **4.3 Generate Historical Snapshots for AI**

A delay model needs history, not just a current status. Create multiple snapshots per project—e.g. every 15 days or every month—and make the backlog evolve over time.

Project X  
01 Jan → 800 pending  
15 Jan → 760  
01 Feb → 745  
15 Feb → 751  
01 Mar → 790  
15 Mar → 842

This allows the model to learn that a rising backlog and declining processing rate are stronger signals than a single static backlog number.

## **4.4 AI Training Dataset**

Create a separate modelling table such as project\_history.csv. The target should be a future outcome, for example elevated delay risk in the next 30 days. Keep evaluation honest: synthetic data should contain noise, missing values and borderline cases.

| Feature | Example |
| :---- | :---- |
| pending\_parcels | 842 |
| average\_stage\_days | 41 |
| sla\_breaches | 53 |
| dispute\_rate | 0.11 |
| processing\_rate\_per\_day | 18 |
| compensation\_pending | 421 |
| possession\_pending | 205 |
| delay\_next\_30d | 1 |

# **5\. Legal & Data-Integrity Guardrails**

| Do not fabricate official recordsSynthetic records should be explicitly labelled as synthetic/demo data. Never present invented projects, landowners, compensation awards or government approvals as genuine government records. |
| :---- |

| Do not overclaim legal calculationsCompensation can depend on the applicable law, state rules and case facts. For the prototype, use illustrative synthetic values unless a value is explicitly derived from a verified legal rule and source. |
| :---- |

| Do not equate anomaly with misconductA high delay/risk score should trigger review, not accuse an owner, officer, contractor or authority of wrongdoing. |
| :---- |

# **6\. Minimum Dataset for a Convincing SIH Demo**

Do not waste the 4-day build trying to recreate India. Build one deep vertical slice with enough data to make the dashboards and models meaningful.

| Component | Recommended demo scale |
| :---- | :---- |
| States | 1 |
| Districts | 3–5 |
| Villages | 15–30 |
| Projects | 10–20 |
| Parcels | 2,000–5,000 |
| Affected families | 1,000–2,000 synthetic |
| Documents | 100–200 |
| Historical snapshots | 20–30 per project |
| Officer/team records | 50–150 synthetic |

## **6.1 Geography Recommendation**

For the demo, use a familiar Indian geography—e.g. Uttar Pradesh or another state with suitable public boundary/infrastructure data. Keep the project scenario explicitly labelled as synthetic unless it is a genuine public project with sourced records.

| Recommended label on the demo“Synthetic acquisition scenario based on real geographic boundaries and infrastructure context.” |
| :---- |

# **7\. The Judge-Convincing Evidence Package**

The most persuasive evidence is not the size of your dataset. It is the completeness of one acquisition case.

PROJECT-001  
  ↓  
Village A  
  ↓  
Parcel 102  
  ↓  
Ownership verified  
  ↓  
Notification issued  
  ↓  
Award made  
  ↓  
Compensation pending  
  ↓  
R\&R completed  
  ↓  
Possession pending  
  ↓  
Risk \+ bottleneck \+ recommendation

* GIS polygon shows where the parcel is.  
* Workflow shows what stage it is in.  
* Document evidence shows why the record exists.  
* Timeline shows what happened and when.  
* Analytics shows why the project is at risk.  
* Decision support shows what should be prioritised.

# **8\. Data Sources Panel to Put Inside BhoomiSetu**

REAL SOURCES  
✓ Department of Land Resources — DILRMP  
✓ LACRRIS  
✓ Survey of India  
✓ Bhuvan / NRSC (where permitted)  
✓ OpenStreetMap  
✓ Public government notifications / legal documents

PROTOTYPE DATA  
✓ Synthetic parcel records  
✓ Synthetic acquisition events  
✓ Synthetic compensation / R\&R records  
✓ Synthetic historical observations  
✓ Synthetic workload / SLA records

# **9\. Recommended Data Architecture**

                    BHOOMISETU DATA LAYER  
                            │  
       ┌────────────────────┼────────────────────┐  
       ▼                    ▼                    ▼  
   REAL CONTEXT         SYNTHETIC OPS        DOCUMENTS  
       │                    │                    │  
 DILRMP / SOI /         Parcels / stages     Notifications  
 LACRRIS / OSM          / payments / R\&R      / reports / awards  
       │                    │                    │  
       └──────────────┬─────┴──────────────┬──────┘  
                      ▼                    ▼  
                 POSTGRESQL \+ POSTGIS   FILE STORE  
                      │                    │  
                      └──────────┬─────────┘  
                                 ▼  
                         ANALYTICS / ML  
                                 │  
               ┌─────────────────┼─────────────────┐  
               ▼                 ▼                 ▼  
          Delay Risk       Bottleneck       Priority Score  
               └─────────────────┼─────────────────┘  
                                 ▼  
                       DECISION SUPPORT UI

# **10\. Suggested 4–5 Day Data Execution Plan**

| Day | Data work | Definition of done |
| :---- | :---- | :---- |
| Day 1 | Collect real boundaries/context; define schema; generate first synthetic dataset | Projects, villages, parcels and lifecycle tables exist |
| Day 2 | Connect GIS; create corridor/parcels; populate documents and status history | Map \+ parcel tracking works |
| Day 3 | Generate historical snapshots; train/evaluate delay-risk model; bottleneck logic | Risk/bottleneck outputs work on held-out synthetic cases |
| Day 4 | Data QA \+ edge cases \+ security validation | No broken geometry, invalid IDs, impossible dates or prediction crashes |
| Day 5 (buffer) | Polish data lineage, citations, demo scenario and fallback dataset | Demo runs without external dependency failures |

# **11\. Data Bottlenecks and Vulnerabilities to Test**

* Missing village/district mapping.  
* Duplicate parcel IDs.  
* Duplicate project IDs.  
* Invalid or self-intersecting polygons.  
* Parcel outside its supposed village/project boundary.  
* Negative/zero area.  
* Completion date earlier than start date.  
* Payment recorded before award without a justified workflow exception.  
* Possession recorded while mandatory predecessor stages are incomplete.  
* Compensation values with impossible magnitudes or units.  
* Missing officer assignment.  
* Historical snapshots with time travel or duplicate dates.  
* Extreme outliers that cause the ML model to overreact.  
* No-history projects where the model should return “insufficient data” rather than invent a risk score.  
* Unauthorized users attempting to view another district/state.  
* Synthetic data accidentally mixed into a “real data” label.

# **12\. Judge Questions About Data — Prepared Answers**

| “Where did your land data come from?”“We use public government/geospatial sources for geographic and programme context, including DoLR/DILRMP and LACRRIS references. For parcel-level workflow history and predictive modelling, we use a clearly labelled synthetic dataset because confidential production records are not publicly available to us.” |
| :---- |

| “Is this real government data?”“The public contextual layers are real. The operational parcel/event records shown in the prototype are synthetic unless explicitly attributed otherwise. We keep that distinction visible in the system.” |
| :---- |

| “Why not use only real data?”“The public sources do not provide the complete longitudinal parcel-level event history required to demonstrate end-to-end workflow and predictive analytics. Synthetic data lets us demonstrate those functions without misrepresenting or exposing sensitive records.” |
| :---- |

| “How will this work in production?”“The database and API layer are designed so authorized departmental feeds can replace prototype tables. The synthetic generator is only the development/testing substitute.” |
| :---- |

| “Can you predict delays accurately with synthetic data?”“We can demonstrate the modelling pipeline and evaluate it on held-out synthetic data, but we will not claim production accuracy. Real deployment performance must be validated on authorized historical departmental records.” |
| :---- |

| “Why do you need GIS?”“GIS lets the system connect acquisition records to the physical project footprint, villages and parcels. It enables spatial prioritisation rather than treating land cases as disconnected rows in a spreadsheet.” |
| :---- |

# **13\. Final Data Checklist Before Demo**

* At least one real public boundary layer is loaded and attributed.  
* DILRMP context metrics are sourced and cited.  
* LACRRIS-inspired schema is used consistently.  
* At least one real/public acquisition document is used where legally/technically appropriate.  
* Synthetic records are explicitly labelled.  
* 2,000–5,000 synthetic parcels exist for the main demo.  
* 10–20 projects exist with distinct bottleneck profiles.  
* Historical snapshots exist for model training/testing.  
* At least one held-out test set exists.  
* GIS geometry validation passes.  
* No impossible lifecycle timestamps remain.  
* No role can access unauthorised geographic scopes.  
* External data sources are not single points of failure for the demo.  
* A backup local dataset can run without internet.  
* One complete project → parcel → document → timeline → risk → recommendation path works.

# **14\. Reference Sources**

Department of Land Resources — LACRRIS public reporting/dashboard — https://larr.dolr.gov.in/faces/public/rptLandAcqProg2.xhtml

Department of Land Resources — LACRRIS dashboard — https://www.larr.dolr.gov.in/faces/common/dashboard.xhtml

DILRMP MIS 3.0 — https://dilrmp.gov.in/dilrmpold/

DILRMP map digitisation / state statistics — https://dilrmp.gov.in/dilrmpold/MapULPIN/MapDiditizaionStateList

Survey of India — Village Boundary Database — https://surveyofindia.gov.in/pages/village-boundary-data-base-of-entire-india

Survey of India — Vector Data Catalogue — https://www.surveyofindia.gov.in/UserFiles/files/Vector%20Data%20Catalog%202025%281%29.pdf

Bhuvan / NRSC — https://bhuvan.nrsc.gov.in/

India Code — Right to Fair Compensation and Transparency in Land Acquisition, Rehabilitation and Resettlement Act, 2013 — https://www.indiacode.nic.in/handle/123456789/2121

Smart India Hackathon — SIH26016 reference — https://sih2026.vuce.in/en/ps/SIH26016

# **15\. Bottom Line**

| The recommended hackathon data strategyUse real data for geography, schema and credibility; use synthetic data for operational depth, historical events and predictive modelling. Build one complete vertical slice, validate the data aggressively, and be explicit with the judge about what is real versus simulated. |
| :---- |

