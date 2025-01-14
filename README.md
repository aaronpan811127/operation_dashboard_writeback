# operations_dashboard_writeback

This is a Databricks app using python Dash framework. It is intended to be used to support operational activity in Databricks lakehouse platform.

The following section outlines high level steps develop the app in local IDE environment

## Getting started

0. Generate sample data in your workspace using setup_data.ipynb notebook. Please change [catalog name] and [schema name] before running the notebook.

### Local dev and test

1. Install the Databricks CLI from https://docs.databricks.com/dev-tools/cli/databricks-cli.html
If you have already installed cli, please make sure it is upgraded to latest version

2. Authenticate to your Databricks workspace, if you have not done so already:
    ```
    $ databricks configure
    ```

3. go to app folder:
    ```
    $ cd [your folder path]/operation_write_back    
    ```

4. Create and activate new virtual environment:
   ```
   $ python3 -m venv .venv/
   $ source .venv/bin/activate
   ```

5. Make sure following folders are added to .gitignore file:
   ```
   .venv/
   .vscode/
   .databricks/
   __pycache__/
   ```

6. Install python package using requirement file
    ```
    $ pip3 install -r requirement.txt    
    ```

7. Setting env variables: a. set DATABRICKS_WAREHOUSE_ID to a sql warehouse in your workspace. b. set SERVICENOW_URL to valid servicenow url, e.g. https://abc.servicenow.com.au/
    ```
    $ export DATABRICKS_WAREHOUSE_ID="[SQL warehouse ID]" 
    $ export SERVICENOW_URL="[ServiceNow URL]" 
    ```

8. Update models.py files. Update table constants with actual table full names in your environments. You may also need to update get_incident_data functions to return data at pipeline execution level if required. 

9. Now you should be ready to continue develop your code (app.py) and test
    ```
    $ python app.py    
    ```

10. Open link to test app. By default, it should be deployed to http://127.0.0.1:8050

### Deploy to Databricks Workspace (Once tested successfully in local environment)

1. Setting env variables: a. set DATABRICKS_WAREHOUSE_ID to a sql warehouse in your workspace. b. set SERVICENOW_URL to valid servicenow url,e.g. https://abc.servicenow.com.au/
    ```
   env:
   - name: "DATABRICKS_WAREHOUSE_ID"
      value: "[SQL warehouse ID]"
   - name: "SERVICENOW_URL"
      value: "[ServiceNow URL]"          
    ```
2. Update models.py files. Update table constants with actual table full names if it is different from dev.

3. Sync to Databricks Workspace. Press ctrl+c when seeing 'Initial Sync Complete' message.
    ```
    $ databricks sync --watch . /Workspace/Users/[your user email]/apps/operations_write_back  
    ```

4. Log in Workspace to validate if the files are synced successfully.

5. Create app if not exist. If app is already created, please start it in apps UI.
    ```
    $ databricks apps create operations-write-back  
    ```

6. Wait for a few mins for app to be created and started

7. Each app will have its own service principal created in Databricks automatically. This sp is used to access all Databricks resources including sql warehouse, UC tables etc. Explicit permission needs to be given to this sp. 

8. Open created app in app UI and locate the sp name and uuid.

9. Update permission.json with sp uuid
    ```
   {
      "access_control_list": [
         {
               "service_principal_name": "[SP UUID]",
               "permission_level": "CAN_RUN"
         }
      ]
   }
    ```

10. Grant sp with access to sql warehouse
    ```
    $ databricks warehouses update-permissions [SQL warehouse ID] --json @permission.json  
    ```

11. Grant sp with access to UC tables using Databricks notebook
    ```
    $ grant use catalog, use schema,select,modify on catalog [catalog name] to `[SP UUID]`   
    ```

12. Now you should be able to deploy the app:
    ```
    $ databricks apps deploy operations-write-back --source-code-path /Workspace/Users/[your user email]/apps/operations_write_back
    ```

13. Open app in app ui and test
