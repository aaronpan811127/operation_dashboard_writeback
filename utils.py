from databricks.sdk.core import Config
from databricks import sql
from datetime import datetime

def sqlQuery(query: str,warehouse_id: str):
    """Execute a SQL query and return the result as a pandas DataFrame."""
    cfg = Config()  # Pull environment variables for auth
    with sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()
        
# Helper function to combine date and time into a timestamp
def combine_datetime(date_str, time_str):
    if date_str and time_str:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
            return datetime.combine(date_obj, time_obj)
        except ValueError:
            return None
    return None       