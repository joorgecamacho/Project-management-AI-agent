"""
Microsoft 365 Client
Handles authentication and API calls to M365 services
"""

import os
import requests
from msal import ConfidentialClientApplication

class M365Client:
    def __init__(self):
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.tenant_id = os.getenv('TENANT_ID')
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        
        self.app = ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        self.token = None
        self._authenticate()
    
    def _authenticate(self):
        """Acquire access token"""
        result = self.app.acquire_token_silent(self.scope, account=None)
        
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            self.token = result["access_token"]
        else:
            raise Exception(f"Authentication failed: {result.get('error_description')}")
    
    def _get_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_emails(self, limit=10, filter_str=None):
        """Retrieve emails from Outlook"""
        url = "https://graph.microsoft.com/v1.0/me/messages"
        params = {
            "$top": limit,
            "$orderby": "receivedDateTime DESC"
        }
        
        if filter_str:
            if filter_str == "unread":
                params["$filter"] = "isRead eq false"
            elif filter_str.startswith("from:"):
                email = filter_str.split("from:")[1].strip()
                params["$filter"] = f"from/emailAddress/address eq '{email}'"
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        
        if response.status_code == 200:
            emails = response.json().get('value', [])
            return {
                "count": len(emails),
                "emails": [
                    {
                        "subject": email['subject'],
                        "from": email['from']['emailAddress']['address'],
                        "received": email['receivedDateTime'],
                        "preview": email.get('bodyPreview', '')[:100],
                        "is_read": email['isRead']
                    }
                    for email in emails
                ]
            }
        else:
            return {"error": f"Failed to retrieve emails: {response.status_code}"}
    
    def send_email(self, to, subject, body):
        """Send an email via Outlook"""
        url = "https://graph.microsoft.com/v1.0/me/sendMail"
        
        email_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to
                        }
                    }
                ]
            }
        }
        
        response = requests.post(url, headers=self._get_headers(), json=email_data)
        
        if response.status_code == 202:
            return {"status": "success", "message": f"Email sent to {to}"}
        else:
            return {"error": f"Failed to send email: {response.status_code}"}
    
    def get_tasks(self, plan_id=None, filter_str=None):
        """Retrieve tasks from Microsoft Planner"""
        # First, get user's plans if no plan_id provided
        if not plan_id:
            plans_url = "https://graph.microsoft.com/v1.0/me/planner/plans"
            response = requests.get(plans_url, headers=self._get_headers())
            
            if response.status_code != 200:
                return {"error": "Failed to retrieve plans"}
            
            plans = response.json().get('value', [])
            if not plans:
                return {"error": "No plans found"}
            
            plan_id = plans[0]['id']  # Use first plan
        
        # Get tasks for the plan
        url = f"https://graph.microsoft.com/v1.0/planner/plans/{plan_id}/tasks"
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 200:
            tasks = response.json().get('value', [])
            
            # Apply filter
            if filter_str == "incomplete":
                tasks = [t for t in tasks if t['percentComplete'] < 100]
            
            return {
                "count": len(tasks),
                "plan_id": plan_id,
                "tasks": [
                    {
                        "id": task['id'],
                        "title": task['title'],
                        "percent_complete": task['percentComplete'],
                        "due_date": task.get('dueDateTime'),
                        "priority": task.get('priority', 5)
                    }
                    for task in tasks
                ]
            }
        else:
            return {"error": f"Failed to retrieve tasks: {response.status_code}"}
    
    def create_task(self, plan_id, title, description=None, due_date=None):
        """Create a new task in Microsoft Planner"""
        # First, get a bucket from the plan
        buckets_url = f"https://graph.microsoft.com/v1.0/planner/plans/{plan_id}/buckets"
        response = requests.get(buckets_url, headers=self._get_headers())
        
        if response.status_code != 200:
            return {"error": "Failed to retrieve buckets"}
        
        buckets = response.json().get('value', [])
        if not buckets:
            return {"error": "No buckets found in plan"}
        
        bucket_id = buckets[0]['id']
        
        # Create task
        url = "https://graph.microsoft.com/v1.0/planner/tasks"
        task_data = {
            "planId": plan_id,
            "bucketId": bucket_id,
            "title": title
        }
        
        if due_date:
            task_data["dueDateTime"] = f"{due_date}T00:00:00Z"
        
        response = requests.post(url, headers=self._get_headers(), json=task_data)
        
        if response.status_code == 201:
            task = response.json()
            
            # Add description if provided
            if description:
                details_url = f"https://graph.microsoft.com/v1.0/planner/tasks/{task['id']}/details"
                details_data = {
                    "description": description
                }
                requests.patch(details_url, headers=self._get_headers(), json=details_data)
            
            return {
                "status": "success",
                "task_id": task['id'],
                "title": task['title']
            }
        else:
            return {"error": f"Failed to create task: {response.status_code}"}
