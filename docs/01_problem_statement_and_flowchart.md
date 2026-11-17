# 01. Problem Statement and High-Level System Flowchart
**Project:** Vehicle Rental Management System (VRMS)  
**Lab:** Software Engineering Lab (CIC-357)  
**Institution:** Maharaja Agrasen Institute of Technology (MAIT), GGSIPU Delhi  

---

## 1. Problem Statement
Many vehicle rental businesses continue to manage bookings, fleet inventory, customer verifications, and payments manually using spreadsheets, paper logbooks, or disconnected point-of-sale systems. This leads to critical operational failures:
1. **Double / Overlapping Bookings:** Simultaneous customer reservations for the same vehicle over conflicting date ranges.
2. **Inaccurate Fleet Availability:** Inability to track when vehicles are undergoing maintenance, retired, or currently rented out.
3. **Payment Reconciliation Errors:** Discrepancies between booking deposits, late-return penalties, and damage fee settlements.
4. **Poor Audit Trails:** Lack of accountability regarding vehicle condition at pickup versus return, odometer readings, and staff sign-offs.

**VRMS** provides a centralized, automated web platform that prevents overlapping bookings through mathematical interval checks, enforces strict finite state machine transitions for vehicles, automates late return fines and damage fee calculation, and optimizes system efficiency using Green Software computing principles.

---

## 2. End-to-End System Flowchart

```mermaid
flowchart TD
    Start([User Arrives at VRMS]) --> AuthCheck{Authenticated?}
    AuthCheck -- No --> LoginRegister[Login / Register]
    LoginRegister --> RoleBranch{Determine User Role}
    AuthCheck -- Yes --> RoleBranch

    %% Customer Branch
    RoleBranch -- Customer --> SearchFleet[Search Fleet with Dates & Type]
    SearchFleet --> OverlapCheck{Overlap Check Passed?}
    OverlapCheck -- No --> ShowUnavailable[Display Alternate Vehicles / Dates]
    ShowUnavailable --> SearchFleet
    OverlapCheck -- Yes --> PricePreview[Preview Rent Calculation & Breakdown]
    PricePreview --> PayDeposit[Process Booking Payment via Gateway]
    PayDeposit --> PaySuccess{Payment Cleared?}
    PaySuccess -- No (TC-07) --> RollbackBooking[Rollback: No Booking Created]
    RollbackBooking --> SearchFleet
    PaySuccess -- Yes (TC-06) --> ConfirmBooking[Create Booking & Transition Vehicle: Available -> Booked]

    %% Rental Staff Branch
    RoleBranch -- Rental Staff --> LookupBooking[Staff Lookups Booking ID]
    LookupBooking --> BookingState{Booking Status}
    
    %% Pickup Flow
    BookingState -- Confirmed --> VerifyLicense[Inspect Driver License & Vehicle]
    VerifyLicense --> RecordStartOdo[Record Start Odometer]
    RecordStartOdo --> HandoverVehicle[Vehicle Handover: Booked -> Rented, Booking Active]
    
    %% Return Flow (UC-08)
    BookingState -- Active --> CheckReturn[Inspect Vehicle & Record End Odometer]
    CheckReturn --> CalcLateFee[Calculate Late Return Days & Fine: 1.5x Daily Tariff]
    CalcLateFee --> DamageInspect{Damage Detected?}
    DamageInspect -- Yes --> AddDamageFee[Assess Damage Fee & Notes]
    DamageInspect -- No --> ZeroDamage[Damage Fee = 0]
    AddDamageFee --> SettleBalance[Calculate Remaining Due: Base + Extras - Paid]
    ZeroDamage --> SettleBalance
    SettleBalance --> CollectFinalPayment[Customer Pays Remaining Due via Gateway]
    CollectFinalPayment --> ReturnPaymentSuccess{Payment Cleared?}
    ReturnPaymentSuccess -- No (7a) --> RetryPayment[Prompt Payment Retry]
    RetryPayment --> CollectFinalPayment
    ReturnPaymentSuccess -- Yes --> UpdateVehicleStatus{Damage > 0?}
    UpdateVehicleStatus -- Yes --> VehMaintenance[Vehicle Status: Under Maintenance]
    UpdateVehicleStatus -- No --> VehAvailable[Vehicle Status: Available]
    VehMaintenance --> GenerateReceipt[Generate Return Receipt & Ledger Entry]
    VehAvailable --> GenerateReceipt

    %% Administrator Branch
    RoleBranch -- Administrator --> AdminDash[Fleet CRUD, Customer List, Revenue & Utilization Analytics]
    AdminDash --> GreenTelemetry[View Green Software Metrics & Carbon Avoided]

    GenerateReceipt --> Finish([End Process])
    GreenTelemetry --> Finish
```
