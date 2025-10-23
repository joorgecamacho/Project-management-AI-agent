# Personal Assistant AI Agent

A Python-based AI agent that manages Microsoft 365 emails and Planner tasks through a CLI interface, using **Ollama** for local LLM inference (no API costs!).

## Features

- **Email Management**: Read, filter, and send emails via Outlook
- **Task Management**: View and create tasks in Microsoft Planner
- **Local AI**: Uses Ollama for private, offline LLM inference
- **CLI Interface**: Simple command-line interaction
- **Cloud Ready**: Designed for Google Cloud Vertex AI Workbench

## Setup

### 1. Install Ollama in Vertex AI Workbench

Open a terminal in your Vertex AI Workbench and run:

```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Pull a model (recommended: llama3.1)
ollama pull llama3.1

# Or use a smaller model for faster inference:
# ollama pull mistral
# ollama pull phi3
```

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

### 2. Microsoft 365 App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations** > **New registration**
3. Name: "Personal Assistant Agent"
4. Supported account types: "Accounts in this organizational directory only"
5. Click **Register**

### 3. Configure API Permissions

1. Go to **API permissions** > **Add a permission**
2. Select **Microsoft Graph** > **Application permissions**
3. Add these permissions:
   - `Mail.Read`
   - `Mail.Send`
   - `Tasks.ReadWrite`
   - `Group.Read.All` (for Planner)
4. Click **Grant admin consent**

### 4. Create Client Secret

1. Go to **Certificates & secrets** > **New client secret**
2. Description: "Assistant Secret"
3. Expires: Choose duration
4. Copy the **Value** (you won't see it again!)

### 5. Get Your IDs

- **Client ID**: On the Overview page (Application ID)
- **Tenant ID**: On the Overview page (Directory ID)

### 6. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 7. Configure Environment Variables

Create a `.env` file:

```env
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
TENANT_ID=your_tenant_id_here
```

## Usage

### Start the Assistant

```bash
python main.py
```

### With Custom Model

```bash
# Use Mistral instead of Llama
python main.py --model mistral

# Use custom Ollama URL
python main.py --ollama-url http://localhost:11434
```

### Example Commands

```
You: Show me my latest 5 emails
You: Do I have any unread emails?
You: Send an email to john@example.com about tomorrow's meeting
You: What tasks do I have?
You: Create a task to review the proposal
You: Show me incomplete tasks
You: clear (clears conversation history)
```

## Recommended Ollama Models

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **llama3.1** | 4.7GB | Medium | High | Best balance |
| **mistral** | 4.1GB | Fast | Good | Quick responses |
| **phi3** | 2.3GB | Very Fast | Good | Limited resources |
| **llama3.1:70b** | 40GB | Slow | Excellent | Maximum quality |

Install with: `ollama pull <model-name>`

## Project Structure

```
├── main.py           # CLI entry point
├── agent.py          # Core AI agent logic (Ollama integration)
├── m365_client.py    # Microsoft 365 API client
├── requirements.txt  # Python dependencies
└── .env             # Environment variables (create this)
```

## Vertex AI Workbench Tips

### Keep Ollama Running

Create a startup script to auto-start Ollama:

```bash
# Create startup script
cat > ~/start_ollama.sh << 'EOF'
#!/bin/bash
ollama serve > /tmp/ollama.log 2>&1 &
EOF

chmod +x ~/start_ollama.sh

# Add to .bashrc
echo '~/start_ollama.sh' >> ~/.bashrc
```

### Monitor Resource Usage

```bash
# Check if Ollama is running
ps aux | grep ollama

# Monitor GPU usage (if available)
nvidia-smi -l 1

# Check memory
free -h
```

### Optimize for Performance

```bash
# Use smaller context window for faster responses
export OLLAMA_NUM_CTX=2048

# Adjust thread count
export OLLAMA_NUM_THREADS=4
```

## Future Enhancements

- Local LLM with Ollama (Done!)
- Jira integration (Planned)
- Calendar management
- Email categorization
- Smart task prioritization
- Optional web interface

## Troubleshooting

### Ollama Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
pkill ollama
ollama serve &

# Check available models
ollama list
```

### Authentication Issues

- Verify all environment variables are set correctly
- Ensure admin consent is granted for API permissions
- Check that client secret hasn't expired

### Permission Errors

- Make sure you've granted the correct Graph API permissions
- Verify admin consent was completed

### Memory Issues

- Use a smaller model (phi3 or mistral)
- Reduce context window: `export OLLAMA_NUM_CTX=2048`
- Clear conversation history with `clear` command

## Why Ollama?

- **Privacy**: All inference happens locally
- **Cost**: No API fees
- **Speed**: Fast responses with good hardware
- **Offline**: Works without internet (after model download)
- **Control**: Full control over model selection

## Notes

- This uses **application permissions** (daemon app), not delegated permissions
- It accesses resources on behalf of the app, not a specific user
- For user-specific access, implement OAuth flow with delegated permissions
- Ollama models run locally and require sufficient RAM/GPU
