# 08. Sequence and Collaboration Diagrams (Booking Flow)
**Project:** Vehicle Rental Management System (VRMS)  
**Lab:** Software Engineering Lab (CIC-357) | MAIT, GGSIPU Delhi  

---

## 1. Sequence Diagram (Booking Flow)

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant UI as Customer Portal UI
    participant Service as BookingService
    participant VDB as VehicleDB / GreenCache
    participant Vehicle as Vehicle Entity
    participant PG as PaymentGateway
    participant DB as Database (SQLAlchemy)

    Customer ->> UI: Select Vehicle #101, Dates (3 Days), Click "Book Now"
    UI ->> Service: bookVehicle(cust_id=201, veh_id=101, p_date, r_date, method)
    
    Service ->> VDB: getVehicle(101)
    VDB -->> Service: vehicle instance (Rate=2500.0)
    
    Service ->> VDB: isVehicleAvailable(101, p_date, r_date)
    Note over VDB, DB: Overlap Check: SELECT COUNT(*) WHERE overlap condition
    VDB -->> Service: True (No overlap)

    Service ->> Service: calculateRent(2500, 3) -> 7500.00
    
    Service ->> PG: makePayment(amount=7500.00, method="Credit Card")
    alt Payment Gateway Approves (TC-06)
        PG -->> Service: {success: True, txn_ref: "TXN-8A9F..."}
        
        Service ->> Vehicle: book_vehicle() [Available -> Booked]
        Vehicle -->> Service: status updated
        
        Service ->> DB: add(Booking #501), add(Payment #701)
        Service ->> DB: commit()
        DB -->> Service: persisted successfully
        
        Service -->> UI: 201 Created (Booking details)
        UI -->> Customer: Display Confirmation & Booking ID #501
    else Payment Gateway Declines (TC-07)
        PG -->> Service: raises PaymentFailedError("Declined")
        Service ->> DB: rollback()
        Service -->> UI: 400 Bad Request ("Payment Failed")
        UI -->> Customer: Display Error Alert (Vehicle remains Available)
    end
```

---

## 2. Collaboration (Communication) Diagram

Illustrating the structural organization of objects participating in the booking workflow with numbered messages:

```mermaid
flowchart LR
    Customer((1: Customer))
    Service((2: BookingService))
    VDB((3: VehicleDB))
    Vehicle((4: Vehicle #101))
    PG((5: PaymentGateway))
    DB[((6: DB / SQLAlchemy))]

    Customer -- "1: bookVehicle(201, 101, 3d)" --> Service
    Service -- "1.1: getVehicle(101)<br>1.2: isVehicleAvailable()" --> VDB
    VDB -- "1.2.1: query overlaps" --> DB
    Service -- "1.3: makePayment(7500)" --> PG
    PG -- "1.3.1: auth approved" --> Service
    Service -- "1.4: book_vehicle()" --> Vehicle
    Service -- "1.5: persist Booking & Payment" --> DB
    Service -- "1.6: return confirmed booking" --> Customer
```
