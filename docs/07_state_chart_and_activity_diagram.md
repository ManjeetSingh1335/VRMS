# 07. State-Chart and Activity Diagram
**Project:** Vehicle Rental Management System (VRMS)  
**Lab:** Software Engineering Lab (CIC-357) | MAIT, GGSIPU Delhi  

---

## 1. Vehicle Finite State Machine (State-Chart Diagram)

```mermaid
stateDiagram-v2
    [*] --> Available : Fleet Ingestion / Admin Add

    Available --> Booked : book_vehicle() [Valid Deposit Paid]
    Booked --> Rented : pickup_vehicle() [Customer Handover]
    
    Rented --> Available : return_vehicle() [Return Verified, No Damage]
    Rented --> Under_Maintenance : report_damage() [Damage Reported during Return]

    Under_Maintenance --> Available : complete_maintenance() [Repairs Finalized]
    
    Available --> Retired : retire_vehicle() [Fleet Decommission]
    Retired --> [*]

    note right of Available
      Any illegal transition (e.g. Available -> Rented
      or Booked -> Retired) raises
      InvalidStateTransitionError.
    end note
```

---

## 2. Activity Diagram with Swimlanes

Demonstrating the integrated operational workflow across the 4 primary actors/subsystems: **Customer, VRMS, Payment Gateway, and Rental Staff**.

```mermaid
flowchart TD
    %% Swimlane Definitions
    subgraph Customer_Lane [Customer]
        C1[Select Vehicle & Rental Dates] --> C2[Submit Booking Request]
        C3[Provide Payment Details]
        C6[Receive Keys & Inspect Car]
        C7[Return Car to Branch Counter]
        C9[Review Final Charges & Settle]
    end

    subgraph VRMS_Lane [VRMS System Engine]
        V1{Dates Available? Overlap Check}
        V2[Compute Rent: daily_rate * days]
        V3{Duration >= 1 day?}
        V4[Initiate Gateway Transaction]
        V5[Transition State: Available -> Booked]
        V6[Create Booking #501 & Payment Record]
        V7[Transition State: Booked -> Rented]
        V8[Create Rental Record with Start Odometer]
        V9[Calculate End Odometer Difference]
        V10{Actual Return > Scheduled?}
        V11[Add Late Fine: 1.5x Daily Tariff]
        V12{Damage Assessed?}
        V13[Add Damage Charge]
        V14[Calculate Balance: Base + Extras - Paid]
        V15{Damage > 0?}
        V16[Transition State: Rented -> Under Maintenance]
        V17[Transition State: Rented -> Available]
        V18[Mark Booking Completed & Generate Return Receipt]
    end

    subgraph Gateway_Lane [Payment Gateway]
        G1[Validate Card / Balance]
        G2{Transaction Approved?}
        G3[Generate Transaction Token]
        G4[Decline: Raise PaymentFailedError]
    end

    subgraph Staff_Lane [Rental Staff]
        S1[Lookup Booking by ID]
        S2[Verify Driver License]
        S3[Record Start Odometer]
        S4[Handover Vehicle Keys]
        S5[Record End Odometer]
        S6[Inspect Vehicle Condition & Notes]
        S7[Hand Over Printed Return Receipt]
    end

    %% Workflow Interconnections
    C2 --> V1
    V1 -- No --> C1
    V1 -- Yes --> V2
    V2 --> V3
    V3 -- Invalid --> C1
    V3 -- Valid --> C3
    C3 --> V4
    V4 --> G1
    G1 --> G2
    G2 -- No (TC-07) --> G4
    G4 --> C3
    G2 -- Yes (TC-06) --> G3
    G3 --> V5
    V5 --> V6

    %% Pickup Phase
    V6 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> V7
    V7 --> V8
    V8 --> S4
    S4 --> C6

    %% Return Phase
    C6 --> C7
    C7 --> S5
    S5 --> V9
    S6 --> V12
    V9 --> V10
    V10 -- Yes --> V11
    V10 -- No --> V12
    V11 --> V12
    V12 -- Yes --> V13
    V12 -- No --> V14
    V13 --> V14
    V14 --> C9
    C9 --> G1
    G3 --> V15
    V15 -- Yes --> V16
    V15 -- No --> V17
    V16 --> V18
    V17 --> V18
    V18 --> S7
```
