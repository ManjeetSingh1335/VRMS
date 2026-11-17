# 10. Deployment Diagram
**Project:** Vehicle Rental Management System (VRMS)  
**Lab:** Software Engineering Lab (CIC-357) | MAIT, GGSIPU Delhi  

---

## 1. Physical Deployment Architecture

```mermaid
flowchart LR
    subgraph Client_Tier ["Tier 1: Client Workstation"]
        Browser["Modern Web Browser (Chrome, Firefox, Edge, Safari)"]
    end

    subgraph App_Server_Tier ["Tier 2: Application Server (Ubuntu 22.04 LTS)"]
        ReverseProxy["Nginx Reverse Proxy & SSL Termination (:443)"]
        WSGI["Gunicorn WSGI Server"]
        FlaskApp["VRMS Flask Application (Python 3.11+, REST API)"]
        InMemCache["Green In-Memory Cache (TTL Engine)"]
        
        ReverseProxy -->|Proxy Pass :5000| WSGI
        WSGI --> FlaskApp
        FlaskApp <--> InMemCache
    end

    subgraph DB_Server_Tier ["Tier 3: Database Server"]
        PgDatabase[("PostgreSQL 15 Database Server (:5432)")]
        PgConnPool["Connection Pooler (PgBouncer)"]
        PgConnPool --> PgDatabase
    end

    subgraph Backup_Tier ["Tier 4: Remote Backup & Disaster Recovery"]
        SFTPStorage["Offsite Backup Storage Server (SFTP :22 / Cloud Volume)"]
    end

    %% Network Connections
    Browser -- "HTTPS (Port 443)<br>TLS 1.3 Encrypted" --> ReverseProxy
    FlaskApp -- "TCP (Port 5432)<br>SQLAlchemy Connection Pool" --> PgConnPool
    PgDatabase -- "Automated pg_dump / Cron<br>SFTP (Port 22) Secure Sync" --> SFTPStorage
```

---

## 2. Infrastructure Specification

| Component | Operating Environment | Port | Protocol | Purpose |
|---|---|---|---|---|
| **Client Workstation** | Windows 10/11, macOS, Linux | Dynamic | HTTPS | User interface access (Customer, Admin, Staff) |
| **Web Server (Reverse Proxy)** | Ubuntu 22.04 LTS / Nginx | 443 | HTTPS | TLS certificate termination, static asset caching |
| **Application Server** | Ubuntu 22.04 LTS / Docker | 5000 | HTTP / WSGI | Flask REST API, domain state machine, green caching |
| **Database Server** | PostgreSQL 15 Engine | 5432 | TCP | ACID relational persistence, CHECK constraints, indexes |
| **Disaster Recovery** | SFTP / Backup Volume | 22 | SFTP | Nightly automated database dumps and schema recovery |
