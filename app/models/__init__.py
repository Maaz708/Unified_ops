# Import all models so SQLAlchemy can resolve string relationship names (e.g. "InventoryUsageLog").
# Import order: mixins first, then all table models so they register with Base before Workspace.
from app.models import mixins  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.automation_rule import AutomationRule  # noqa: F401
from app.models.automation_run import AutomationRun  # noqa: F401
from app.models.availability_slot import AvailabilitySlot  # noqa: F401
from app.models.booking import Booking  # noqa: F401
from app.models.booking_type import BookingType  # noqa: F401
from app.models.contact import Contact  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.event_log import EventLog  # noqa: F401
from app.models.form_submission import FormSubmission  # noqa: F401
from app.models.form_template import FormTemplate  # noqa: F401
from app.models.inventory_item import InventoryItem  # noqa: F401
from app.models.inventory_usage_log import InventoryUsageLog  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.users import StaffUser  # noqa: F401
from app.models.workspace_email_config import WorkspaceEmailConfig  # noqa: F401
from app.models.workspace import Workspace  # noqa: F401
