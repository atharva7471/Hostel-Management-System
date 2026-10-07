from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum
from typing import Optional, List

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.str_schema()

class RoleEnum(str, Enum):
    MANAGEMENT = "MANAGEMENT"
    STUDENT = "STUDENT"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: RoleEnum
    name: str

class UserInDB(UserCreate):
    hashed_password: str

class UserResponse(BaseModel):
    email: EmailStr
    role: RoleEnum
    name: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: RoleEnum

# --- Phase 2 Models ---

class StudentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    GRADUATED = "GRADUATED"
    ACTIVE_RESIDENT = "ACTIVE_RESIDENT"

class ApplicationStatus(str, Enum):
    INCOMPLETE = "INCOMPLETE"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"

class StudentProfile(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    full_name: str
    student_id: str
    email: EmailStr
    phone: str
    course: str
    year: str
    status: StudentStatus = StudentStatus.ACTIVE
    
    # Phase 6: Onboarding Fields
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    preferred_hostel: Optional[str] = None
    preferred_room_type: Optional[str] = None
    preferred_floor: Optional[str] = None
    special_requirements: Optional[str] = None
    
    application_status: ApplicationStatus = ApplicationStatus.INCOMPLETE
    resident_id: Optional[str] = None
    allocation_date: Optional[str] = None
    
    # Allocations
    allocated_hostel_id: Optional[str] = None
    allocated_room_id: Optional[str] = None
    allocated_room_number: Optional[str] = None
    allocated_bed_number: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)

class Hostel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    building: str
    floors: int
    description: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)

class RoomStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    FULL = "FULL"
    MAINTENANCE = "MAINTENANCE"

class BedStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"

class Bed(BaseModel):
    bed_number: str
    status: BedStatus = BedStatus.AVAILABLE
    student_id: Optional[str] = None
    student_email: Optional[str] = None
    student_name: Optional[str] = None

class Room(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    hostel_id: str
    room_number: str
    floor: int
    capacity: int
    status: RoomStatus = RoomStatus.AVAILABLE
    beds: List[Bed] = []

    model_config = ConfigDict(populate_by_name=True)

# --- Phase 3 Models ---

class FeeStatus(str, Enum):
    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"

class Fee(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    student_id: str
    academic_year: str
    fee_amount: float
    amount_paid: float = 0.0
    remaining_amount: float
    due_date: str # ISO string
    status: FeeStatus = FeeStatus.PENDING

    model_config = ConfigDict(populate_by_name=True)

class PaymentMethod(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    UPI = "UPI"
    CARD = "CARD"

class PaymentStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PENDING = "PENDING"

class Payment(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    fee_id: str
    student_id: str
    amount: float
    payment_date: str # ISO string
    payment_id: str # MOCK-1234
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.COMPLETED

    model_config = ConfigDict(populate_by_name=True)

# --- Phase 4 Models ---

class RequestStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class RequestPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class ComplaintCategory(str, Enum):
    ROOM = "ROOM"
    FOOD = "FOOD"
    WATER = "WATER"
    ELECTRICITY = "ELECTRICITY"
    CLEANLINESS = "CLEANLINESS"
    SECURITY = "SECURITY"
    OTHER = "OTHER"

class MaintenanceCategory(str, Enum):
    PLUMBING = "PLUMBING"
    ELECTRICAL = "ELECTRICAL"
    FURNITURE = "FURNITURE"
    FAN_AC = "FAN_AC"
    INTERNET = "INTERNET"
    BATHROOM = "BATHROOM"
    OTHER = "OTHER"

class BaseRequest(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str
    description: str
    location: str
    priority: RequestPriority
    status: RequestStatus = RequestStatus.SUBMITTED
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    room_id: Optional[str] = None
    hostel_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class Complaint(BaseRequest):
    category: ComplaintCategory
    model_config = ConfigDict(populate_by_name=True)

class MaintenanceRequest(BaseRequest):
    category: MaintenanceCategory
    model_config = ConfigDict(populate_by_name=True)

# --- Phase 5 Models ---

class NotificationType(str, Enum):
    PAYMENT = "PAYMENT"
    COMPLAINT = "COMPLAINT"
    MAINTENANCE = "MAINTENANCE"
    ALLOCATION = "ALLOCATION"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    GENERAL = "GENERAL"

class Notification(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    title: str
    message: str
    type: NotificationType
    is_read: bool = False
    related_id: Optional[str] = None
    created_at: str

    model_config = ConfigDict(populate_by_name=True)

class AnnouncementPriority(str, Enum):
    NORMAL = "NORMAL"
    IMPORTANT = "IMPORTANT"
    URGENT = "URGENT"

class Announcement(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str
    description: str
    priority: AnnouncementPriority = AnnouncementPriority.NORMAL
    target_audience: str = "ALL" # "ALL" or hostel_id
    created_at: str

    model_config = ConfigDict(populate_by_name=True)

# --- Phase 7 Models ---

class MovementStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    OUTSIDE = "OUTSIDE"
    RETURNED = "RETURNED"
    REJECTED = "REJECTED"
    LATE_RETURN = "LATE_RETURN"

class MovementReason(str, Enum):
    GOING_HOME = "Going Home"
    COLLEGE = "College"
    PERSONAL = "Personal"
    MEDICAL = "Medical"
    OTHER = "Other"

class Movement(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    student_id: str
    resident_id: str
    hostel_id: str
    room_id: str
    bed_id: str
    student_name: str
    
    reason: MovementReason
    destination: str
    expected_exit: str
    expected_return: str
    note: Optional[str] = None
    
    status: MovementStatus = MovementStatus.PENDING
    
    actual_exit: Optional[str] = None
    actual_return: Optional[str] = None
    
    requested_at: str
    approved_by: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)

class MovementCreate(BaseModel):
    reason: MovementReason
    destination: str
    expected_exit: str
    expected_return: str
    note: Optional[str] = None

