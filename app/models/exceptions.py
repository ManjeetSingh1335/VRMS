"""Custom domain exceptions for Vehicle Rental Management System (VRMS)."""

class VRMSError(Exception):
    """Base exception for VRMS domain errors."""
    pass

class InvalidStateTransitionError(VRMSError):
    """Raised when an illegal vehicle state transition is attempted."""
    pass

class InvalidDurationError(VRMSError):
    """Raised when rental duration is less than 1 day."""
    pass

class VehicleNotFoundError(VRMSError):
    """Raised when a vehicle cannot be found."""
    pass

class VehicleUnavailableError(VRMSError):
    """Raised when a vehicle is already booked, rented, or undergoing maintenance."""
    pass

class PaymentFailedError(VRMSError):
    """Raised when payment amount <= 0 or payment gateway declines transaction."""
    pass

class BookingNotFoundError(VRMSError):
    """Raised when booking is not found."""
    pass

class UnauthorizedActionError(VRMSError):
    """Raised when user role is not authorized for an action."""
    pass
