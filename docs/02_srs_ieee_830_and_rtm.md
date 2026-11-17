# 02. Software Requirements Specification (SRS) - IEEE 830 Standard
**Project:** Vehicle Rental Management System (VRMS)  
**Standard:** IEEE Std 830-1998  
**Lab:** Software Engineering Lab (CIC-357) | MAIT, GGSIPU Delhi  

---

## 1. Introduction
### 1.1 Purpose
This document provides the formal software requirements specification for the **Vehicle Rental Management System (VRMS)**, an automated fleet booking, payment, and rental tracking system.

### 1.2 Scope
VRMS provides customer registration, fleet catalog search with overlap prevention, mock payment gateway integration, staff vehicle pickup and return workflows (UC-08), administrative fleet CRUD, financial reporting, and green software computing optimizations.

---

## 2. Overall Description
### 2.1 Product Perspective
VRMS operates as an independent, multi-tier web application built on Python 3.11+ (Flask REST API), SQLAlchemy ORM, SQLite/PostgreSQL, and responsive vanilla HTML5/CSS3/JavaScript.

### 2.2 User Characteristics
- **Customer:** General public booking vehicles, making deposits, and monitoring active rentals.
- **Rental Staff:** Branch operators conducting physical vehicle inspection, recording odometers, and handling settlements.
- **Administrator:** Fleet managers managing vehicle catalogs, customer registries, and auditing revenue.

---

## 3. Specific Functional Requirements
- **FR-1 Customer Management:** Account registration, secure password hashing (PBKDF2/Werkzeug), authentication, profile updating (name, phone, address, driving license).
- **FR-2 Vehicle Management:** Administrator capabilities to add, edit, categorize (Sedan, SUV, Hatchback, Luxury, Truck), inspect, and retire vehicles.
- **FR-3 Vehicle Availability & Overlap Prevention:** Query fleet inventory for a date range $[P, R]$; strictly reject overlapping reservations:
  $$\text{Overlap} \iff (\text{Existing.Pickup} \le R) \land (\text{Existing.Return} \ge P) \land (\text{Status} \in \{\text{'Confirmed'}, \text{'Active'}\})$$
- **FR-4 Booking Management:** Calculate rent duration ($days \ge 1$), compute tariff, confirm reservations, cancel per policy (10% fee), refund deposit.
- **FR-5 Payment Management:** Atomic payment transactions with mock gateway, support partial payments, record transaction references and payment status.
- **FR-6 Pickup and Return (UC-08):** Staff records start odometer on pickup ($Booked \to Rented$); inspects vehicle on return, assesses late fees (1.5x daily tariff per late day) and damage charges, settles balance, updates vehicle state ($Available$ or $Under\ Maintenance$), generates official return receipt.
- **FR-7 Reports and Audit:** Administrative reporting dashboard with visual charts for revenue by payment method, vehicle utilization percentage, and fleet status breakdown.

---

## 4. Non-Functional Requirements
- **NFR-1 Performance:** API search and booking response time $< 2.0$ seconds.
- **NFR-2 Reliability & Backup:** Automated database backup script (`scripts/backup.py`, `scripts/backup.sh`) and point-in-time recovery (`scripts/restore.py`).
- **NFR-3 Security:** Hashed passwords using salt, role-based access control (RBAC), SQL injection prevention via parameterized ORM queries, XSS sanitization.
- **NFR-4 Usability:** Responsive viewport design supporting mobile, tablet, and desktop viewports.
- **NFR-5 Green Computing (Exp. 15):** In-memory TTL cache for vehicle lookups, projection-only search payload, database indexing on status and dates.

---

## 5. Requirements Traceability Matrix (RTM)

| Req ID | Requirement Description | Design Module / Class | API Route / Endpoint | Test Case / Verification |
|---|---|---|---|---|
| **FR-1** | Customer Registration & Profile | `Customer`, `auth.py` | `/register`, `/api/auth/profile` | Manual UI demo, `test_customer_reg` |
| **FR-2** | Vehicle Fleet Inventory CRUD | `Vehicle`, `VehicleDB` | `/api/admin/vehicles` | `TestVehicleOperations.test_retire_vehicle` |
| **FR-3** | Overlap Prevention Algorithm | `VehicleDB.isVehicleAvailable` | `/api/vehicles/search` | `TestVRMSIntegration.test_tc08`, `TestDataFlow.test_df02` |
| **FR-4** | Booking & Duration Calculation | `BookingService.bookVehicle` | `/api/bookings/create` | `TestVRMSIntegration.test_tc06`, `TestDataFlow.test_df01` |
| **FR-5** | Atomic Payment & Failure Rollback | `PaymentGateway`, `Payment` | `/api/bookings/create` | `TestVRMSIntegration.test_tc07`, `TestVehicleOperations.test_tc04,05` |
| **FR-6** | Pickup & Return Settlement (UC-08) | `BookingService.returnVehicle` | `/api/staff/return`, `/receipt/<id>` | `TestVRMSIntegration.test_full_rental_lifecycle` |
| **FR-7** | Revenue & Utilization Reports | `admin_routes.py`, Chart.js | `/api/admin/reports` | Admin dashboard verification |
| **NFR-1**| Response Time $< 2$ seconds | Flask, SQLAlchemy | All endpoints | `run_tests.py` ($19$ tests in $<2.0$s) |
| **NFR-2**| Backup & Disaster Recovery | `scripts/backup.py` | CLI execution | `vrms/backups/*.db` file verification |
| **NFR-3**| Password Security & RBAC | `werkzeug.security`, `@role_required` | All protected endpoints | Session & route access tests |
| **NFR-5**| Green Software Architecture | `GreenCache`, `green_metrics.py` | `/api/green-metrics` | `scripts/green_metrics.py` ($99\%$ DB read reduction) |
