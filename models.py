from utils import sqlQuery
from databricks.sdk.core import Config
from databricks import sql

# Define full table name constants. To be updated to actual table names in deployed environment
# EXECUTION_LOG_TABLE: existing table that captures dlt pipeline execution logs. Used to read and validate pipeline id and execution id and provide additional context when assigning incidents.
EXECUTION_LOG_TABLE = "aaron_demo.default.dlt_pipeline_execution_log"
# EXECUTION_INCIDENT_TABLE: table that captures incident assigned to dlt pipeline executions (usually failed ones). 1 pipeline execution should have max 1 incident.
EXECUTION_INCIDENT_TABLE = "aaron_demo.default.dlt_pipeline_incidents"        

def get_incident_data(pipeline_id: str, execution_id: str,warehouse_id:str):
    '''
    Get current incident assignment by left outer join log table with incident table. Used to read and validate pipeline id and execution id. Also provide additional context when assigning incidents.
    The returned result should have grain of pipeline id and execution id
    '''
    query = f"""SELECT l.pipeline_id
                ,l.execution_id
                ,l.pipeline_name
                ,i.incident_id
                ,i.incident_status
                ,i.incident_comments
                ,i.assigned_to
                ,i.assigned_timestamp 
                FROM {EXECUTION_LOG_TABLE} AS l 
                LEFT OUTER JOIN {EXECUTION_INCIDENT_TABLE} AS i 
                ON l.pipeline_id = i.pipeline_id and l.execution_id = i.execution_id
                WHERE l.pipeline_id = '{pipeline_id}' AND l.execution_id = '{execution_id}'
            """
    return sqlQuery(query,warehouse_id)

def write_incident(data: list,columns: str,warehouse_id: str):
    '''
    Construct validate SQL to update incident table
    '''    
    cfg = Config()  # Pull environment variables for auth    
    with sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate
    ) as connection:
        with connection.cursor() as cursor:
            # Create a temporary table from the list
            temp_view = f"""
                CREATE OR REPLACE TEMPORARY VIEW source_data AS
                SELECT * FROM VALUES
                {str(data)[1:-1]}
                AS t({columns})
            """
            print(temp_view)
            cursor.execute(temp_view)

            
            # Perform the MERGE operation
            merge_query = f"""
            MERGE INTO  {EXECUTION_INCIDENT_TABLE} AS t
            USING source_data AS s
            ON t.pipeline_id = s.pipeline_id 
            AND t.execution_id = s.execution_id
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
            """            
            print(merge_query)
            cursor.execute(merge_query)
            connection.commit()
