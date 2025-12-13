import importlib.metadata

from nhs_waiting_lists.models.base import Base

__app_name__ = "nhs_waiting_lists"
__version__ = importlib.metadata.version(__app_name__)


from nhs_waiting_lists.utils.canned_queries import get_consolidated_df, get_consolidated_df2
