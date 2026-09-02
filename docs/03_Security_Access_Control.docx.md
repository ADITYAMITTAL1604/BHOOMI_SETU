# **BhoomiSetu — Security & Access Control Document**

**Project:** BhoomiSetu — Real-Time National Land Acquisition & Management System

**Problem Statement:** SIH26016 | SIH 2026

**Version:** 1.0

**Date:** 2026-09-01

**Classification:** Internal — Team Use Only

────────────────────────────────────────────────────────────

## **1\. Security Philosophy**

BhoomiSetu handles sensitive government land acquisition data including parcel ownership records, compensation amounts, R\&R beneficiary details, and administrative decisions. Security is not an afterthought — it is embedded into every layer.

**Core Principles:**

* **Least Privilege** — Every user sees only what their role and geographic scope permits  
* **Defense in Depth** — Multiple layers of security controls  
* **Audit Everything** — Every critical action is logged with before/after state  
* **Fail Secure** — On error, deny access rather than grant it  
* **Human Accountability** — AI is advisory; decisions are attributed to authorized officers

────────────────────────────────────────────────────────────

## **2\. Role-Based Access Control (RBAC) Architecture**

### **2.1 Role Hierarchy**

                    ADMIN  
                      │  
                   CENTRAL  
                      │  
                    STATE  
                      │  
                   DISTRICT  
                   ╱       ╲  
         PROJECT\_AGENCY   FIELD\_OFFICER

### **2.2 Role Definitions**

| Role | Scope | Description |
| :---- | :---- | :---- |
| ADMIN | National (all data) | System administrator. Full access to all data, user management, audit logs, workflow templates. Cannot make acquisition decisions. |
| CENTRAL | National (read) | Ministry-level officer. Read-only national view. Can create projects. Cannot modify parcel data. |
| STATE | State-specific | State-level officer. Full access within their assigned state. Can create projects, manage parcels, upload documents. |
| DISTRICT | District-specific | District collector / land acquisition officer. Full access within their assigned district. Transition stages, manage parcels. |
| PROJECT\_AGENCY | Project-specific | NHAI, Railways, Smart City SPV. Read access to assigned project(s). Upload documents. Cannot modify workflow. |
| FIELD\_OFFICER | Assigned parcels | Tehsildar, survey officer. Update parcel data, transition stages, upload documents for assigned parcels only. |

### **2.3 Geographic Scope Enforcement**

Every data query is filtered by the user's scope. This is enforced at the **service layer** (not just UI).

class ScopeFilter:  
    """Applied to every database query involving geographic data."""  
      
    def apply(self, query, user):  
        if user.role in ("ADMIN", "CENTRAL"):  
            return query  \# No filter — national scope  
          
        if user.role \== "STATE":  
            return query.filter(Model.state \== user.state\_scope)  
          
        if user.role \== "DISTRICT":  
            return query.filter(  
                Model.state \== user.state\_scope,  
                Model.district \== user.district\_scope  
            )  
          
        if user.role \== "PROJECT\_AGENCY":  
            return query.filter(  
                Model.project\_id.in\_(user.assigned\_project\_ids)  
            )  
          
        if user.role \== "FIELD\_OFFICER":  
            return query.filter(  
                Model.assigned\_officer \== user.id  
            )  
          
        \# Fail secure: deny all if role is unknown  
        raise PermissionDeniedError("Unknown role")

*🔴 CAUTION:*

*Geographic scope filtering MUST be applied at the database query level (backend service layer), not at the API response level. A frontend-only filter is trivially bypassed.*

### **2.4 Full Permission Matrix**

| Action | ADMIN | CENTRAL | STATE | DISTRICT | PROJECT\_AGENCY | FIELD\_OFFICER |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| Authentication |  |  |  |  |  |  |
| Login | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manage users | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Projects |  |  |  |  |  |  |
| View all projects | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View own-scope projects | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Create project | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Edit project | ✅ | ✅ | ✅ (own) | ❌ | ❌ | ❌ |
| Delete/archive project | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Parcels |  |  |  |  |  |  |
| View parcels (scoped) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (assigned) |
| Create parcel | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Edit parcel | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ (assigned) |
| Transition stage | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ (assigned) |
| Documents |  |  |  |  |  |  |
| Upload | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| View (scoped) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (assigned) |
| Delete | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Dashboards |  |  |  |  |  |  |
| National dashboard | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| State dashboard | ✅ | ✅ | ✅ (own) | ❌ | ❌ | ❌ |
| District dashboard | ✅ | ✅ | ✅ (own) | ✅ (own) | ❌ | ❌ |
| Project dashboard | ✅ | ✅ | ✅ (own) | ✅ (own) | ✅ (own) | ❌ |
| Analytics |  |  |  |  |  |  |
| View risk/bottleneck | ✅ | ✅ | ✅ (own) | ✅ (own) | ✅ (own) | ❌ |
| View intervention | ✅ | ❌ | ✅ (own) | ✅ (own) | ❌ | ❌ |
| System |  |  |  |  |  |  |
| View audit log | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage workflows | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| System settings | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

────────────────────────────────────────────────────────────

## **3\. Authentication Implementation**

### **3.1 JWT Token Architecture**

┌────────────────────────────────────────┐  
│            ACCESS TOKEN                │  
│  Header: { alg: HS256, typ: JWT }      │  
│  Payload: {                            │  
│    sub: "user\_uuid",                   │  
│    username: "officer\_01",             │  
│    role: "DISTRICT",                   │  
│    state\_scope: "Uttar Pradesh",       │  
│    district\_scope: "Gautam Buddha N.", │  
│    iat: \<issued\_at\>,                   │  
│    exp: \<issued\_at \+ 60min\>            │  
│  }                                     │  
│  Signature: HMAC-SHA256(secret)        │  
└────────────────────────────────────────┘

┌────────────────────────────────────────┐  
│           REFRESH TOKEN                │  
│  Stored server-side (DB)               │  
│  Expiry: 7 days                        │  
│  Single-use: invalidated after refresh │  
│  Bound to user \+ device fingerprint    │  
└────────────────────────────────────────┘

### **3.2 Token Lifecycle**

Login (POST /auth/login)  
    → Validate credentials (bcrypt compare)  
    → Generate access token (60 min)  
    → Generate refresh token (7 days, stored in DB)  
    → Return both tokens  
    → Create audit log entry

API Request  
    → Extract Bearer token from Authorization header  
    → Verify JWT signature and expiration  
    → Extract user claims (role, scope)  
    → Apply scope filter to query  
    → If expired → return 401

Token Refresh (POST /auth/refresh)  
    → Validate refresh token exists in DB  
    → Validate not expired  
    → Invalidate old refresh token  
    → Issue new access \+ refresh tokens  
    → Create audit log entry

Logout (POST /auth/logout)  
    → Invalidate refresh token in DB  
    → Add access token to short-term blacklist (Redis/in-memory)  
    → Create audit log entry

### **3.3 Password Security**

\# Password requirements  
MIN\_LENGTH \= 8  
REQUIRE\_UPPERCASE \= True  
REQUIRE\_LOWERCASE \= True  
REQUIRE\_DIGIT \= True  
REQUIRE\_SPECIAL \= True  \# @, \#, $, %, etc.

\# Hashing  
ALGORITHM \= "bcrypt"  
ROUNDS \= 12  \# bcrypt cost factor

\# Storage: NEVER store plaintext passwords  
password\_hash \= bcrypt.hash(password, rounds=12)

### **3.4 Session Management**

| Setting | Value | Rationale |
| :---- | :---- | :---- |
| Access token expiry | 60 minutes | Balance usability and security |
| Refresh token expiry | 7 days | Avoid frequent re-login |
| Max concurrent sessions | 3 per user | Prevent credential sharing |
| Failed login lockout | 5 attempts → 15 min lockout | Brute-force protection |
| Idle timeout | 30 minutes (frontend) | Auto-logout on inactivity |

────────────────────────────────────────────────────────────

## **4\. API Security**

### **4.1 Input Validation**

Every API endpoint validates input using Pydantic schemas with strict constraints:

class ParcelCreate(BaseModel):  
    """Strict input validation for parcel creation."""  
      
    project\_id: UUID  
    survey\_number: str \= Field(  
        min\_length=1, max\_length=50,   
        pattern=r'^\[A-Za-z0-9/\\-\]+$'  \# Alphanumeric \+ / and \-  
    )  
    area\_ha: float \= Field(gt=0, le=100000)  \# Positive, max 100K hectares  
    owner\_name: str \= Field(min\_length=1, max\_length=200)  
    village: str \= Field(min\_length=1, max\_length=100)  
    district: str \= Field(min\_length=1, max\_length=100)  
    state: str \= Field(min\_length=1, max\_length=100)  
    geometry: dict  \# Validated as GeoJSON separately  
      
    @validator('geometry')  
    def validate\_geojson(cls, v):  
        """Validate GeoJSON structure and geometry."""  
        if v.get('type') not in ('Polygon', 'MultiPolygon'):  
            raise ValueError('Geometry must be Polygon or MultiPolygon')  
        \# Validate coordinates are within India bounds  
        \# Validate polygon is valid (no self-intersection)  
        return v

### **4.2 SQL Injection Prevention**

\# ALWAYS use parameterized queries through SQLAlchemy ORM  
\# ✅ CORRECT  
result \= session.query(Parcel).filter(Parcel.project\_id \== project\_id).all()

\# ❌ NEVER DO THIS  
result \= session.execute(f"SELECT \* FROM parcel WHERE project\_id \= '{project\_id}'")

### **4.3 CORS Configuration**

app.add\_middleware(  
    CORSMiddleware,  
    allow\_origins=\["http://localhost:3000"\],  \# Frontend only  
    allow\_credentials=True,  
    allow\_methods=\["GET", "POST", "PUT", "DELETE"\],  
    allow\_headers=\["Authorization", "Content-Type"\],  
    max\_age=600,  \# Preflight cache: 10 minutes  
)

### **4.4 Rate Limiting**

| Endpoint Category | Limit | Window |
| :---- | :---- | :---- |
| Authentication | 10 requests | 1 minute |
| Standard API | 100 requests | 1 minute |
| File upload | 10 requests | 1 minute |
| Analytics (heavy) | 30 requests | 1 minute |
| GIS queries | 60 requests | 1 minute |

### **4.5 Request Size Limits**

\# FastAPI middleware  
MAX\_REQUEST\_BODY \= 1 \* 1024 \* 1024      \# 1MB for JSON requests  
MAX\_FILE\_UPLOAD \= 10 \* 1024 \* 1024       \# 10MB for file uploads  
MAX\_GEOJSON\_SIZE \= 5 \* 1024 \* 1024       \# 5MB for GeoJSON uploads

────────────────────────────────────────────────────────────

## **5\. File Upload Security**

### **5.1 Validation Pipeline**

File received  
    → Check Content-Type header  
    → Check file extension  
    → Check magic bytes (file signature)  
    → Validate file size ≤ 10MB  
    → Scan for embedded scripts (PDF, DOCX)  
    → Compute SHA-256 hash  
    → Rename to: {entity\_type}/{entity\_id}/{uuid}.{ext}  
    → Store in controlled directory (NOT web-accessible)  
    → Save metadata to DB  
    → Serve via authenticated API endpoint only

### **5.2 Allowed File Types**

| Type | Extensions | Magic Bytes |
| :---- | :---- | :---- |
| PDF | .pdf | %PDF- |
| PNG | .png | \\x89PNG |
| JPEG | .jpg, .jpeg | \\xFF\\xD8\\xFF |
| DOCX | .docx | PK\\x03\\x04 (ZIP) |
| XLSX | .xlsx | PK\\x03\\x04 (ZIP) |

### **5.3 File Storage Security**

/app/documents/                    \# NOT served directly by web server  
├── projects/{project\_id}/  
│   ├── {uuid}.pdf  
│   └── {uuid}.png  
├── parcels/{parcel\_id}/  
│   ├── {uuid}.pdf  
│   └── {uuid}.jpg  
└── temp/                          \# Cleared hourly

*⚠️ IMPORTANT:*

*Files are NEVER stored with user-provided filenames. They are renamed to UUIDs to prevent path traversal attacks. The original filename is stored in the database metadata only.*

────────────────────────────────────────────────────────────

## **6\. GIS Security**

### **6.1 Geometry Validation**

def validate\_geometry(geojson: dict) \-\> bool:  
    """Validate GeoJSON before database insertion."""  
      
    \# 1\. Valid GeoJSON structure  
    if geojson.get('type') not in ('Polygon', 'MultiPolygon'):  
        raise ValueError("Invalid geometry type")  
      
    \# 2\. Coordinate bounds (India bounding box)  
    INDIA\_BOUNDS \= {  
        'min\_lon': 68.0, 'max\_lon': 98.0,  
        'min\_lat': 6.0,  'max\_lat': 38.0  
    }  
    for coord in extract\_coordinates(geojson):  
        if not (INDIA\_BOUNDS\['min\_lon'\] \<= coord\[0\] \<= INDIA\_BOUNDS\['max\_lon'\]):  
            raise ValueError("Longitude out of India bounds")  
        if not (INDIA\_BOUNDS\['min\_lat'\] \<= coord\[1\] \<= INDIA\_BOUNDS\['max\_lat'\]):  
            raise ValueError("Latitude out of India bounds")  
      
    \# 3\. Valid polygon (no self-intersection)  
    \# Using PostGIS: SELECT ST\_IsValid(geometry)  
      
    \# 4\. Reasonable size (no geometry \> 10,000 vertices)  
    vertex\_count \= count\_vertices(geojson)  
    if vertex\_count \> 10000:  
        raise ValueError("Geometry too complex (max 10,000 vertices)")  
      
    \# 5\. Non-zero area  
    \# Using PostGIS: SELECT ST\_Area(geometry) \> 0  
      
    return True

### **6.2 GIS Query Protection**

\# Viewport-based loading: limit results per request  
MAX\_PARCELS\_PER\_QUERY \= 500  
MAX\_BOUNDING\_BOX\_AREA \= 10  \# square degrees (\~100,000 sq km)

\# Prevent full-table spatial scans  
if bbox\_area(envelope) \> MAX\_BOUNDING\_BOX\_AREA:  
    raise ValueError("Bounding box too large. Zoom in for parcel data.")

────────────────────────────────────────────────────────────

## **7\. Encryption**

### **7.1 In Transit**

| Layer | Protocol | Details |
| :---- | :---- | :---- |
| Client ↔ API | HTTPS (TLS 1.2+) | For production; HTTP acceptable for local hackathon demo |
| API ↔ Database | Local socket / TLS | Docker network (trusted); TLS for remote DB |

### **7.2 At Rest**

| Data | Encryption | Details |
| :---- | :---- | :---- |
| Passwords | bcrypt (12 rounds) | One-way hash; never reversible |
| JWT secret | Environment variable | Never committed to code |
| Documents | Filesystem permissions | OS-level access control |
| Database | PostgreSQL native encryption | pgcrypto for sensitive fields (future) |

### **7.3 Sensitive Data Handling**

SENSITIVE\_FIELDS \= \[  
    "owner\_name",  
    "beneficiary\_name",  
    "compensation.assessed\_amount",  
    "compensation.paid\_amount",  
    "password\_hash"  
\]

\# These fields are:  
\# \- Never logged in plaintext in audit logs (masked: "\*\*\*")  
\# \- Never included in error responses  
\# \- Only returned to authorized roles  
\# \- Excluded from analytics/ML feature sets

────────────────────────────────────────────────────────────

## **8\. Audit Logging**

### **8.1 What Gets Logged**

| Action Category | Examples |
| :---- | :---- |
| Authentication | Login, logout, failed login, token refresh, password change |
| Data Modification | Create/update/delete project, parcel, stage transition |
| Document Operations | Upload, download, delete |
| Administrative | User creation, role change, workflow template change |
| Access Violations | Unauthorized access attempts, scope violations |
| System Events | ML model retrain, data seed, schema migration |

### **8.2 Audit Log Schema**

{  
  "log\_id": "uuid",  
  "timestamp": "2026-09-01T12:30:00Z",  
  "user\_id": "uuid",  
  "username": "district\_officer\_01",  
  "role": "DISTRICT",  
  "action": "PARCEL\_STAGE\_TRANSITION",  
  "entity\_type": "PARCEL",  
  "entity\_id": "uuid",  
  "previous\_state": {  
    "current\_stage": "VERIFICATION",  
    "status": "IN\_PROGRESS"  
  },  
  "new\_state": {  
    "current\_stage": "NOTIFICATION",  
    "status": "IN\_PROGRESS"  
  },  
  "ip\_address": "192.168.1.100",  
  "user\_agent": "Mozilla/5.0...",  
  "metadata": {  
    "reason": "Verification complete per officer inspection"  
  }  
}

### **8.3 Audit Log Integrity**

\# Audit logs are:  
\# \- Append-only (no UPDATE or DELETE allowed)  
\# \- Indexed by timestamp, user, entity  
\# \- Retained for minimum 1 year  
\# \- Accessible only to ADMIN role  
\# \- Cannot be modified by any user including ADMIN (insert-only table)

\# Database constraint  
"""  
REVOKE UPDATE, DELETE ON audit\_log FROM bhoomisetu\_app;  
GRANT INSERT, SELECT ON audit\_log TO bhoomisetu\_app;  
"""

────────────────────────────────────────────────────────────

## **9\. OWASP Top-10 Mitigation Summary**

| \# | Vulnerability | Mitigation |
| :---- | :---- | :---- |
| A01 | Broken Access Control | RBAC \+ geographic scope enforcement at service layer |
| A02 | Cryptographic Failures | bcrypt passwords, JWT HS256, TLS in transit |
| A03 | Injection | SQLAlchemy ORM (parameterized queries), Pydantic validation |
| A04 | Insecure Design | Scope filter middleware, fail-secure defaults |
| A05 | Security Misconfiguration | Docker env isolation, no default credentials, CORS whitelist |
| A06 | Vulnerable Components | Pin dependency versions, review before adding |
| A07 | Auth Failures | Rate limiting login, account lockout, token expiry |
| A08 | Data Integrity Failures | File hash verification, audit log immutability |
| A09 | Logging Failures | Comprehensive audit logging, structured log format |
| A10 | Server-Side Request Forgery | No user-controlled URL fetching; GIS tiles from whitelist only |

────────────────────────────────────────────────────────────

## **10\. Security Testing Checklist**

### **10.1 Authentication Tests**

* ☐ Login with valid credentials → access granted  
* ☐ Login with wrong password → 401, account lockout after 5 attempts  
* ☐ Login with non-existent user → 401 (generic error, no user enumeration)  
* ☐ Access API without token → 401  
* ☐ Access API with expired token → 401  
* ☐ Access API with tampered token → 401  
* ☐ Refresh token reuse after rotation → 401 (token invalidated)

### **10.2 Authorization / Scope Tests**

* ☐ District officer cannot access another district's parcels → 403  
* ☐ State officer cannot access another state's data → 403  
* ☐ Field officer cannot access unassigned parcels → 403  
* ☐ Project agency cannot modify parcel workflow → 403  
* ☐ Central officer cannot create parcels → 403  
* ☐ Non-admin cannot access audit logs → 403  
* ☐ Non-admin cannot manage users → 403  
* ☐ Direct API calls bypass frontend scope filtering → still blocked by backend

### **10.3 Input Validation Tests**

* ☐ SQL injection in search/filter parameters → rejected  
* ☐ XSS payload in project/parcel names → sanitized  
* ☐ Oversized request body (\>1MB) → 413  
* ☐ Invalid GeoJSON geometry → 400  
* ☐ Self-intersecting polygon → 400  
* ☐ Coordinates outside India bounds → 400  
* ☐ Negative parcel area → 400  
* ☐ Completion date before start date → 400  
* ☐ Non-UUID in ID parameters → 400

### **10.4 File Upload Tests**

* ☐ Upload disallowed file type (.exe, .js, .sh) → 400  
* ☐ Upload file with spoofed extension (rename .exe to .pdf) → rejected (magic byte check)  
* ☐ Upload file \> 10MB → 413  
* ☐ Path traversal in filename (../../etc/passwd) → sanitized (UUID rename)  
* ☐ Direct access to /documents/ directory → 403 (not web-accessible)

### **10.5 GIS Security Tests**

* ☐ Malformed GeoJSON → 400  
* ☐ Geometry with 100,000+ vertices → 400  
* ☐ Bounding box covering entire country → 400 (too large)  
* ☐ Invalid SRID → 400

### **10.6 AI/ML Security Tests**

* ☐ Prediction request for out-of-scope project → 403  
* ☐ Prediction with insufficient data → returns "insufficient data" (not fabricated score)  
* ☐ Extreme outlier input → model returns with degraded confidence, not crash  
* ☐ Model inference does not leak training data

────────────────────────────────────────────────────────────

## **11\. Incident Response (Demo Context)**

| Scenario | Response |
| :---- | :---- |
| Unauthorized access detected | Log event, return 403, alert admin |
| Repeated failed logins | Lock account 15 minutes, log event |
| Suspicious file upload | Reject upload, log event with file details |
| Database connection failure | Return 503, retry with exponential backoff |
| JWT secret compromise | Rotate secret, invalidate all tokens, force re-login |

────────────────────────────────────────────────────────────

## **12\. Demo User Accounts**

| Username | Role | State Scope | District Scope | Purpose |
| :---- | :---- | :---- | :---- | :---- |
| admin | ADMIN | — | — | System administration |
| central\_officer | CENTRAL | — | — | National dashboard demo |
| up\_state\_officer | STATE | Uttar Pradesh | — | State-level demo |
| gbn\_district\_officer | DISTRICT | Uttar Pradesh | Gautam Buddha Nagar | District workflow demo |
| nhai\_project | PROJECT\_AGENCY | — | — | Project agency view |
| field\_officer\_01 | FIELD\_OFFICER | Uttar Pradesh | Gautam Buddha Nagar | Field operations demo |

*⚠️ WARNING:*

*All demo accounts use \*\*non-trivial passwords\*\* (not "password123"). Default credentials are generated by the seed script and stored in a \`.env.demo\` file that is \*\*not\*\* committed to version control.*