# Vehicle Rental Management System (VRMS)
### Software Engineering Lab (CIC-357) | MAIT, GGSIPU Delhi
**Author / GitHub Account:** [@ManjeetSingh1335](https://github.com/ManjeetSingh1335)  
**Repository:** [https://github.com/ManjeetSingh1335/vrms](https://github.com/ManjeetSingh1335/vrms)

---

## 1. Project Overview
**Vehicle Rental Management System (VRMS)** is an enterprise-grade full-stack web application designed to eliminate double-bookings, automate fleet lifecycle transitions, streamline customer reservations, manage return inspections with late fines/damage charges (UC-08), and reduce computational energy consumption via Green Software architecture.

---

## 2. Key Features
- **FR-1 Customer Management:** Registration, login, profile management (driving license, phone, address).
- **FR-2 Vehicle Management:** Admin fleet catalog CRUD (Sedan, SUV, Hatchback, Luxury, Truck).
- **FR-3 Overlap Prevention:** Mathematical interval check preventing conflicting bookings for the same vehicle.
- **FR-4 Booking Management:** Real-time tariff calculation ($Rate \times Days$, $Days \ge 1$), cancellation policy (10% fee).
- **FR-5 Payment Management:** Atomic mock payment gateway; failure triggers automatic booking rollback.
- **FR-6 Pickup & Return (UC-08):** Staff odometer capture, late return fine calculation (1.5x daily tariff), damage fee assessment, balance settlement, printable return receipt.
- **FR-7 Reports & Business Intelligence:** Interactive Chart.js charts for revenue by payment method, fleet status distribution, and vehicle utilization.
- **Exp. 15 Green Software Computing:** In-memory TTL caching, projection-only queries, and real-time carbon telemetry (`/api/green-metrics`) slashing database reads by 99%.

---

## 3. Technology Stack
- **Backend:** Python 3.11+ with Flask REST API, Flask-SQLAlchemy ORM, Werkzeug password hashing
- **Database:** SQLite (local development) / PostgreSQL 15 (Docker & production), 3NF normalized schema with CHECK constraints
- **Frontend:** Vanilla HTML5, CSS3 (responsive grid, modern cards, modals, badges), vanilla JavaScript, Chart.js
- **Testing:** Python `unittest` test suite (Unit, Integration, and Data Flow tests)
- **Containerization:** Docker & Docker Compose (`Dockerfile`, `docker-compose.yml`)

---

## 4. Quick Start & Setup

### A. Clone and Install Dependencies
```bash
git clone https://github.com/ManjeetSingh1335/vrms.git
cd vrms

# Create virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### B. Seed Sample Data
```bash
python scripts/seed.py
```
*Seeds 1 Administrator, 1 Rental Staff, 2 Customers, and 10 realistic fleet vehicles.*

### C. Run Application
```bash
python run.py
```
Open your browser at: **`http://127.0.0.1:5000`**

---

## 5. Pre-Configured Demo Login Credentials

| Role | Name | Email | Password | Pre-Configured Actions |
|---|---|---|---|---|
| **Administrator** | Rajesh Sharma | `admin@vrms.com` | `admin123` | Fleet CRUD, view customer ledger, analytics charts |
| **Rental Staff** | Vikram Malhotra | `staff@vrms.com` | `staff123` | Lookup bookings, handover pickup, process return (UC-08) |
| **Customer 1** | Aarav Mehta | `aarav@gmail.com` | `cust123` | Customer ID 201, search fleet, book, pay, cancel |
| **Customer 2** | Priya Sharma | `priya@gmail.com` | `cust123` | Customer ID 202, book and test overlap rejection |

*(Quick 1-click buttons are available on the login page to automatically fill credentials).*

---

## 6. Automated Testing (100% Passing)

Run the unified test runner:
```bash
python tests/run_tests.py
```
### Test Suite Breakdown:
1. **`tests/test_vehicle_operations.py` (Unit & State Machine Tests):**
   - **TC-01:** Vehicle 101 availability initially returns `Available=True`
   - **TC-02:** Reserve transitions `Available` $\to$ `Booked`
   - **TC-03:** Return transitions `Rented` $\to$ `Available`
   - **TC-04:** Payment of 7500 $\to$ Success
   - **TC-05:** Payment of 0 $\to$ Fail (`PaymentFailedError`)
   - **ECP & Boundary Tests:** Invalid state transitions, 0 days, negative days, maintenance recovery
2. **`tests/test_vrms_integration.py` (Integration Tests):**
   - **TC-06:** Customer 201 + Vehicle 101 for 3 days $\to$ creates Booking #501 with 7500 rent
   - **TC-07:** Payment failure $\to$ booking not created (atomic rollback)
   - **TC-08:** Booking an already booked vehicle in overlapping timeframe $\to$ rejected
   - **Full Rental Lifecycle:** Book $\to$ Pickup $\to$ Return with late fee & receipt generation
3. **`tests/test_data_flow.py` (Data Flow DU-Chain Tests):**
   - **DF-01:** Valid booking path (Vehicle 101, 3 days)
   - **DF-02:** Overlapping vehicle unavailable path
   - **DF-03:** Days = 0 invalid duration path
   - **DF-04:** Payment gateway failure path
   - **DF-05:** Vehicle ID 999 not found path
   - **DF-06:** Calculation path ($2500 \times 3 = 7500$)

---

## 7. Green Software Computing Benchmark (Exp. 15)
Run the green computing comparison benchmark:
```bash
python scripts/green_metrics.py
```
**Results:**
- **DB Reads Avoided:** 99.0% reduction (500 queries reduced to 5)
- **Cache Hit Ratio:** 99.0%
- **Data Transfer:** 53.4% reduction via selective field projection
- **Execution Speed:** 98.2% speedup
- **Estimated Carbon Saved:** ~75.2 mg $CO_2$ per 100 requests

---

## 8. Database Backup & Disaster Recovery (NFR-2)
```bash
# Create SQLite backup
python scripts/backup.py

# Restore from latest backup
python scripts/restore.py

# Docker / Linux PostgreSQL backup
bash scripts/backup.sh
```

---

## 9. Docker Deployment
```bash
docker compose up --build
```
Access the application at `http://localhost:5000`.

---

## 10. Complete Documentation Artifacts (`/docs`)
1. [01. Problem Statement & Flowchart](docs/01_problem_statement_and_flowchart.md)
2. [02. IEEE 830 SRS & Requirements Traceability Matrix](docs/02_srs_ieee_830_and_rtm.md)
3. [03. DFD Level 0, Level 1 & Structure Chart](docs/03_dfd_and_structure_chart.md)
4. [04. ER Diagram & 3NF Relational Schema](docs/04_er_diagram_and_schema.md)
5. [05. Use Case Diagram & Formal UC-08 Spec](docs/05_use_case_and_uc08_spec.md)
6. [06. Class Diagram & Object Diagram](docs/06_class_and_object_diagrams.md)
7. [07. State-Chart & Activity Diagram](docs/07_state_chart_and_activity_diagram.md)
8. [08. Sequence & Collaboration Diagrams](docs/08_sequence_and_collaboration_diagrams.md)
9. [09. Component Diagram](docs/09_component_diagram.md)
10. [10. Deployment Diagram](docs/10_deployment_diagram.md)
11. [11. Function Point Analysis & Effort Estimation](docs/11_function_point_analysis.md)
12. [12. Project Management: WBS, Gantt, and PERT/CPM](docs/12_project_management_wbs_gantt_pert.md)
13. [13. Data Flow Testing (DEF-USE & DU-Chains)](docs/13_data_flow_testing.md)
