import uuid
from datetime import datetime
from ..models.exceptions import PaymentFailedError

class PaymentGateway:
    """Mock simulated external payment gateway service."""
    
    @classmethod
    def makePayment(cls, amount: float, method: str = "Credit Card", simulate_failure: bool = False) -> dict:
        """Process a simulated payment.
        
        Rules:
        - Payment amount must be > 0.
        - If amount <= 0, raises PaymentFailedError("Payment Failed: Amount must be greater than 0.")
        - If simulate_failure is True, raises PaymentFailedError("Payment Failed: Gateway declined transaction.")
        """
        if amount is None or amount <= 0:
            raise PaymentFailedError("Payment Failed: Amount must be greater than 0.")
            
        if simulate_failure:
            raise PaymentFailedError("Payment Failed: Gateway declined transaction.")
            
        txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        return {
            "success": True,
            "transaction_ref": txn_id,
            "amount": round(float(amount), 2),
            "payment_method": method,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "Completed"
        }
        
    @classmethod
    def refundPayment(cls, transaction_ref: str, amount: float) -> dict:
        """Process a simulated refund."""
        if amount is None or amount <= 0:
            raise PaymentFailedError("Refund Failed: Amount must be greater than 0.")
            
        refund_id = f"REF-{uuid.uuid4().hex[:10].upper()}"
        return {
            "success": True,
            "refund_ref": refund_id,
            "original_txn": transaction_ref,
            "refund_amount": round(float(amount), 2),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "Refunded"
        }
