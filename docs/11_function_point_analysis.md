# 11. Function Point (FP) Analysis & Effort Estimation
**Project:** Vehicle Rental Management System (VRMS)  
**Lab:** Software Engineering Lab (CIC-357) | MAIT, GGSIPU Delhi  

---

## 1. Unadjusted Function Point (UFP) Calculation

Function Points measure the functional size of software based on the user's external functional perspective according to IFPUG standards.

### Functional Units Classification Table

| Function Component | Count | Complexity Rating | Weight Multiplier | Unadjusted Function Points (UFP) |
|---|---|---|---|---|
| **External Inputs (EI)** | 8 | Average | 4 | $8 \times 4 = 32$ |
| **External Outputs (EO)** | 7 | Average | 5 | $7 \times 5 = 35$ |
| **External Inquiries (EQ)** | 7 | Average | 4 | $7 \times 4 = 28$ |
| **Internal Logical Files (ILF)** | 4 | Average | 10 | $4 \times 10 = 40$ |
| **External Interface Files (EIF)**| 2 | Average | 7 | $2 \times 7 = 14$ |
| **Total Unadjusted Function Points (UFP)** | | | | **142** |

#### Detailed Decomposition:
- **8 External Inputs (EI):** Customer Register, Customer Login, Update Profile, Add Vehicle, Edit Vehicle, Retire Vehicle, Create Booking, Record Return & Odometer.
- **7 External Outputs (EO):** Booking Confirmation, Return Receipt, Payment Receipt, Fleet Status Report, Revenue by Payment Method, Top Booked Vehicles Report, Cancellation Notice.
- **7 External Inquiries (EQ):** Search Vehicles with Dates/Types, View Single Vehicle Specs, Lookup Customer Bookings, Lookup Booking by ID for Staff, Admin View Customers, Admin View All Payments, Query Green Telemetry.
- **4 Internal Logical Files (ILF):** Customer Table, Vehicle Table, Booking Table, Rental Table.
- **2 External Interface Files (EIF):** Payment Gateway Interface (mock external token provider), External Notification / Mail Interface.

---

## 2. Value Adjustment Factor (VAF) & Adjusted Function Points (AFP)

### 14 General System Characteristics (GSCs) Rating (Scale 0 to 5)

| # | General System Characteristic (GSC) | Degree of Influence (DI) | Justification |
|---|---|---|---|
| C1 | Data Communications | 4 | Distributed REST API over HTTP/HTTPS |
| C2 | Distributed Data Processing | 3 | Separate web application and database tiers |
| C3 | Performance Objectives | 4 | Under 2.0s search & booking latency (NFR-1) |
| C4 | Heavily Used Configuration | 3 | Concurrent multi-user bookings |
| C5 | Transaction Rate | 4 | Continuous customer rentals and return processing |
| C6 | On-Line Data Entry | 5 | 100% interactive web data entry forms |
| C7 | End-User Efficiency | 4 | Single-page tabs, quick autofill, responsive layout |
| C8 | On-Line Update | 4 | Immediate vehicle state updates upon booking/return |
| C9 | Complex Processing Logic | 4 | FSM state machine, overlap math algorithm, late fee |
| C10| Reusability | 3 | Modular blueprint design and reusable services |
| C11| Installation Ease | 3 | Automated Docker Compose and seed script |
| C12| Operational Ease | 4 | Automated backup, recovery, and self-contained seed |
| C13| Multiple Sites | 3 | Multi-branch rental staff counter support |
| C14| Facilitate Change | 4 | Green software caching and decoupled microservices |
| **Total** | **Total Degree of Influence (TDI)** | **48** | |

### Computation:
$$\text{TDI} = \sum_{i=1}^{14} C_i = 48$$

$$\text{Value Adjustment Factor (VAF)} = 0.65 + (0.01 \times \text{TDI}) = 0.65 + (0.01 \times 48) = \mathbf{1.13}$$

$$\text{Adjusted Function Points (AFP)} = \text{UFP} \times \text{VAF} = 142 \times 1.13 = \mathbf{160.46 \approx 160}$$

---

## 3. Effort, Duration, and Team Sizing Estimation (COCOMO II Mapping)

Based on industry productivity averages for modern high-level languages (Python / Flask: $\approx 8 \text{ FP / person-month}$):

### Effort Calculation:
$$\text{Effort} = \frac{\text{AFP}}{\text{Productivity Rate}} = \frac{160.46}{8.0} \approx \mathbf{20.1\text{ person-months}}$$

### Project Schedule Duration:
Using standard software engineering schedule estimation formula:
$$\text{Duration} = 3.0 \times (\text{Effort})^{0.33} = 3.0 \times (20.06)^{0.33} = 3.0 \times 2.60 \approx \mathbf{7.8\text{ months}}$$

### Optimal Team Size:
$$\text{Team Size} = \frac{\text{Effort}}{\text{Duration}} = \frac{20.06}{7.8} \approx \mathbf{2.57 \approx 3\text{ engineers}}$$
