"""
Personal Assistant Agent
Core logic for processing requests and managing tools
Uses Ollama for local LLM inference
"""

import json
import requests
from m365_client import M365Client

class PersonalAssistant:
    def __init__(self, ollama_model="llama3.1", ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.m365 = M365Client()
        self.conversation_history = []
        
        # Test Ollama connection
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code != 200:
                print(f"⚠️  Warning: Cannot connect to Ollama at {ollama_url}")
        except Exception as e:
            print(f"⚠️  Warning: Ollama connection failed: {e}")
        
        self.tools = [
            {
                "name": "get_emails",
                "description": "Retrieve emails from Outlook inbox. Returns list of recent emails.",
                "parameters": {
                    "limit": "Number of emails to retrieve (default 10)",
                    "filter": "Filter criteria: 'unread' for unread emails, 'from:email@example.com' for specific sender"
                }
            },
            {
                "name": "send_email",
                "description": "Send an email via Outlook",
                "parameters": {
                    "to": "Recipient email address (required)",
                    "subject": "Email subject (required)",
                    "body": "Email body content (required)"
                }
            },
            {
                "name": "get_tasks",
                "description": "Retrieve tasks from Microsoft Planner",
                "parameters": {
                    "plan_id": "Planner plan ID (optional, will use first plan if not provided)",
                    "filter": "Filter: 'incomplete' for incomplete tasks, 'due_soon' for tasks due soon"
                }
            },
            {
                "name": "create_task",
                "description": "Create a new task in Microsoft Planner",
                "parameters": {
                    "plan_id": "Planner plan ID (required)",
                    "title": "Task title (required)",
                    "description": "Task description (optional)",
                    "due_date": "Due date in YYYY-MM-DD format (optional)"
                }
            }
        ]
    
    def _create_system_prompt(self):
        """Create system prompt with tool descriptions"""
        tools_desc = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tools
        ])
        
        return f"""You are a helpful personal assistant with access to Microsoft 365.
You can help manage emails and Planner tasks.

Available tools:
{tools_desc}

When you need to use a tool, respond ONLY with a JSON object in this format:
{{"tool": "tool_name", "parameters": {{"param1": "value1", "param2": "value2"}}}}

If you don't need a tool, respond normally in a friendly, concise way.
Format information clearly for CLI display.

Examples:
User: "Show me my emails"
Assistant: {{"tool": "get_emails", "parameters": {{"limit": 10}}}}

User: "What's the weather?"
Assistant: I can help you with emails and tasks from Microsoft 365, but I don't have access to weather information.
"""
    
    def _call_ollama(self, messages):
        """Call Ollama API"""
        url = f"{self.ollama_url}/api/chat"
        
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return response.json()['message']['content']
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    def process_request(self, user_input):
        """Process user request and return response"""
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        messages = [
            {"role": "system", "content": self._create_system_prompt()}
        ] + self.conversation_history
        
        # Get initial response from LLM
        response_text = self._call_ollama(messages)
        
        # Check if response is a tool call
        if self._is_tool_call(response_text):
            try:
                tool_call = json.loads(response_text)
                tool_name = tool_call.get('tool')
                parameters = tool_call.get('parameters', {})
                
                # Execute tool
                tool_result = self.execute_tool(tool_name, parameters)
                
                # Add tool result to conversation
                self.conversation_history.append({
                    "role": "assistant",
                    "content": f"[Used tool: {tool_name}]"
                })
                
                self.conversation_history.append({
                    "role": "user",
                    "content": f"Tool result: {json.dumps(tool_result, indent=2)}\n\nPlease summarize this information in a clear, friendly way for the user."
                })
                
                # Get final response
                messages = [
                    {"role": "system", "content": self._create_system_prompt()}
                ] + self.conversation_history
                
                final_response = self._call_ollama(messages)
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_response
                })
                
                return final_response
                
            except json.JSONDecodeError:
                # Not a valid tool call, treat as normal response
                pass
        
        # Normal response (no tool needed)
        self.conversation_history.append({
            "role": "assistant",
            "content": response_text
        })
        
        return response_text
    
    def _is_tool_call(self, text):
        """Check if response is a tool call"""
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            try:
                data = json.loads(text)
                return 'tool' in data
            except:
                return False
        return False
    
    def execute_tool(self, function_name, arguments):
        """Execute the requested tool"""
        try:
            if function_name == "get_emails":
                return self.m365.get_emails(
                    limit=arguments.get('limit', 10),
                    filter_str=arguments.get('filter')
                )
            elif function_name == "send_email":
                return self.m365.send_email(
                    to=arguments['to'],
                    subject=arguments['subject'],
                    body=arguments['body']
                )
            elif function_name == "get_tasks":
                return self.m365.get_tasks(
                    plan_id=arguments.get('plan_id'),
                    filter_str=arguments.get('filter')
                )
            elif function_name == "create_task":
                return self.m365.create_task(
                    plan_id=arguments['plan_id'],
                    title=arguments['title'],
                    description=arguments.get('description'),
                    due_date=arguments.get('due_date')
                )
            else:
                return {"error": f"Unknown function: {function_name}"}
        except Exception as e:
            return {"error": str(e)}
