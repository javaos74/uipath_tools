import requests
import json

class UiPathConnection:

    """Base class for initial functions and storing authentication credentials"""

    def __init__(self, url, orgname, username, password, oauth=False, tenant_logical_name='', client_id='', client_secret='', scope=''):

        """Initialize the class

        Keyword Arguments:
            url: URL of the orchestrator
            tenant: Name of tenant to connect to
            username: username of the admin
            password: password for the username

        NOTE: These parameters only need to be entered if you are on the cloud version of UiPath

            url: "https://platform.uipath.com/[Account Logical Name]/[Tenant Logical Name]"
            cloud: Needs to be set to True if this is the cloud platform
            tenant_logical_name: Can be found on the website for your tenant
            client_id: can be found on the website for your tenant
            user_key: can be found on the website


        """
        self.base_url = url
        self.orgname = orgname
        self.oauth = oauth
        self.tenant_logical_name = tenant_logical_name
        self.token = self._authenticate(username, password, orgname, tenant_logical_name, client_id, client_secret, scope)
        print(self.token)

    def _authenticate(self, username, password, orgname, tenant_logical_name, client_id, client_secret, scope):

        """Authenticate. This will store the token for future usage as the authentication method for UiPath Rest
        API is Bearer Token authentication.

        There are two types of authentication.  One for cloud or automation suite environments and one for Legacy Windows orchestrator.  The following
        accounts for this.

        """

        if self.oauth:
            endpoint = f"{self.base_url}/identity_/connect/token"
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
             
            payload = f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}&scope={scope}"
            r = requests.post( endpoint, data=payload, headers=headers, verify=False)
            #print( endpoint, payload, r, r.text)
            if r.status_code == 200:
                return_value = r.json()
                print('Authenticated')
                return return_value['access_token']
        else:
            payload = str(
                    {"tenancyName": orgname,
                     "usernameOrEmailAddress": username,
                     "password": password}
                         )
            headers = {'content-type': 'application/json'}
            url = self.base_url + '/api/Account/Authenticate'
            r = requests.post(url, data=payload, headers=headers, verify=False)

            if r.status_code == 200:
                return_value = r.json()
                print('Authenticated')
                return return_value['result']
            else:
                raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])

    def get_release_key(self, folder, job_name):
        ''' Get process release key '''
        if self.token is None:
            raise ValueError("You must authenticate first")

        url = f'{self.base_url}/{self.orgname}/{self.tenant_logical_name}/orchestrator_/odata/Releases?$filter=contains(Name, \'{job_name}\')'
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token,'X-UIPATH-OrganizationUnitId': folder['Id']}

        r = requests.get(url, headers=headers, verify=False)
        result = r.json()

        try:
            release_key = result['value'][0]['Key']
        except KeyError:
            print(result) 
        except IndexError:
            print(result)
            raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])

        return release_key

    def start_job(self, release_key, folder, inputs=None):
        """Starts a job with the given release key"""

        if self.token is None:
            raise ValueError("You must authenticate first")

        url = f'{self.base_url}/{self.orgname}/{self.tenant_logical_name}/orchestrator_/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs'
        headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.token, 'X-UIPATH-OrganizationUnitId': folder['Id']}

        if inputs is not None:
            payload = str(
                            {
                                "startInfo": {
                                    "ReleaseKey": release_key,
                                    "InputArguments": inputs
                                   }
                            }
                          )
        else:
            payload = str(
                            {
                                "startInfo": {
                                    "ReleaseKey": release_key
                                   }
                            }
                          )
        r = requests.post(url, data=payload, headers=headers)

        if r.status_code == 201:
            print('Robot Job has successfully been initiated')
            return True
        else:
            raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])

    def _get_running_job_id(self, release_name):

        """Helper function to get the ID of the running job in question.  This will pass back to the
        job function to Kill the Job"""

        if self.token is None:
            raise ValueError("You must authenticate first")

        url = f'{self.base_url}/{self.orgname}/{self.tenant_logical_name}/orchestrator_/odata/Jobs?$filter=contains(ReleaseName, \'{release_name}\') and State eq \'Running\''
        headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.token}

        r = requests.get(url, headers=headers)
        result = r.json()

        if r.status_code == 200:
            try:
                running_job_id = result['value'][0]['Id']

                # Return the Job Id back to the stopJob function
                return running_job_id
            except IndexError:
                raise IndexError('Please make sure the name of the job is correct and the job is running')

        else:
            raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])

    def stop_job(self, release_name):
        """This will hard kill a job that needs to be stopped"""

        if self.token is None:
            raise ValueError("You must authenticate first")

        job_id = self._get_running_job_id(release_name)

        url = f'{self.base_url}/{self.orgname}/{self.tenant_logical_name}/orchestrator_/odata/Jobs({job_id})/UiPath.Server.Configuration.OData.StopJob'
        headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.token}
        payload = str({
                        "strategy": "Kill"
                      })
        r = requests.post(url, data=payload, headers=headers)

        if r.status_code == 200:
            print('robot job has successfully been terminated')
        else:
            raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])

    def start_transaction(self, queue_name):
        """This will start the most recent transaction for this queue.  You can add variables but that has
        not been implemented just yet"""

        if self.token is None:
            raise ValueError("You must authenticate first")

        url = f'{self.base_url}/{self.orgname}/{self.tenant_logical_name}/orchestrator_/odata/Queues/UiPathODataSvc.StartTransaction'
        headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.token}
        payload = str({
                "transactionData": {
                    "Name": queue_name,
                            }
                       })
        r = requests.post(url, data=payload, headers=headers)

        if r.status_code == 204:
            print('Transaction has successfully been initiated')
        else:
            raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])

    def create_machine(self, machine_name, description):

        """This will create a machine with the specified parameters"""

        if self.token is None:
            raise ValueError("You must authenticate first")

        url = f'{self.base_url}/{self.orgname}/{self.tenant_logical_name}/orchestrator_/odata/Machines'
        headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.token}
        payload = str({
                      "Name": machine_name,
                      "Description": description,
                      "Type": "Standard"
                      })
        r = requests.post(url, data=payload, headers=headers)

        if r.status_code == 201:
            print('Machine has successfully been created')
        else:
            raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])

    def create_robot(self, machine_name, robot_name, username, password, description,
                     robot_type='Attended', hosting_type='Standard'):

        """This will create a robot with the specified parameters"""

        if self.token is None:
            raise ValueError("You must authenticate first")

        url = f'{self.base_url}/{self.orgname}/{self.tenant_logical_name}/orchestrator_/odata/Robots'
        headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.token}
        payload = str({
                        "MachineName": machine_name,
                        "Name": robot_name,
                        "Username": username,
                        "Description": description,
                        "Type": robot_type,
                        "HostingType": hosting_type,
                        "Password": password
                      })
        r = requests.post(url, data=payload, headers=headers)

        if r.status_code == 201:
            print('Robot has successfully been created')
        else:
            raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])

            
    def get_folders(self):
        '''This get all folder information'''
        folders = []

        if self.token is None:
            raise ValueError("You must authenticate first")

        url = f'{self.base_url}/{self.orgname}/{self.tenant_logical_name}/orchestrator_/odata/Folders'
        #print(url)
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token}

        r = requests.get(url, headers=headers, verify=False)
        print(r.status_code, r.text)
        result = r.json()

        if r.status_code == 200:
            for f in result['value']:
                folders.append( { 'FullyQualifiedName': f['FullyQualifiedName'], 'Id':f['Id']})
            return folders
        else:
            raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])


    def add_queue_items(self, queue_name, folder, reference, item):
        ''' Add queue item on specific queue'''
        payload = {
            'itemData': {
                'Name': queue_name,
                'SpecificContent': {
                },
                'Reference': reference
            }
        }
        for kv in item.keys():
            payload['itemData']['SpecificContent'][kv] = item[kv]
        if self.token is None:
            raise ValueError("You must authenticate first")

        url = f'{self.base_url}/{self.orgname}/{self.tenant_logical_name}/orchestrator_/odata/Queues/UiPathODataSvc.AddQueueItem'
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token, 'X-UIPATH-OrganizationUnitId': str(folder['Id'])}

        r = requests.post(url, headers=headers, json=payload, verify=False)
        print(r.status_code, r.text)
        result = r.json()

        if r.status_code == 201:
            print("new QueueItem sucessfully added")
        else:
            raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])
        return result

    def get_queueitem_status(self, key, folder):
        ''' Get queueitem status '''
        payload = {
            
        } 
        if self.token is None:
            raise ValueError("You must authenticate first")

        url = f'{self.base_url}/{self.orgname}/{self.tenant_logical_name}/orchestrator_/odata/QueueItems({key})'
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token, 'X-UIPATH-OrganizationUnitId': str(folder['Id'])}

        r = requests.get(url, headers=headers, json=payload, verify=False)
        print(r.status_code, r.text)
        if r.status_code == 200:
            print("GetQueueItems successfully processed")
            result = r.json()
            return result
        else:
            raise ValueError("Server Error: " + str(r.status_code) + '.  ' + r.json()['message'])

       