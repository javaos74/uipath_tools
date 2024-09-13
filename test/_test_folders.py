import os, time
from uipath_tools import uipathorchestratorapi as uip
from dotenv import load_dotenv

load_dotenv()

con = uip.UiPathConnection( os.environ['ORCHESTRATOR_URL'], os.environ['ORG_NAME'], 
                            os.environ['USER_NAME'], os.environ['PASSWORD'],
                           True, os.environ['TENANT_NAME'], os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'], os.environ['SCOPE'])
folders = con.get_folders()
folder = {'Id': 1493557, 'Name': 'Shared'} 
data = {'postNum': '1211360334160'}
qi = con.add_queue_items( "ToolCallingQ", folder, "PostOffice", data)
print(qi)
while True:
    qstatus = con.get_queueitem_status( qi['Id'], folder)
    print(qstatus)
    time.sleep(3)
    
