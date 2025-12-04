# Streamlit Setup Guide - AWS Migration Assistant

## Overview

A user-friendly web interface for the AWS Migration Assistant, built with Streamlit.

## Features

### 🎯 Core Features
- **Interactive Chat Interface**: Natural conversation with the migration assistant
- **Session Management**: Maintains conversation context across multiple queries
- **Architecture Diagrams**: Visual display of generated AWS diagrams
- **Quick Actions**: Pre-built example prompts for common tasks
- **Image Download**: Download generated diagrams directly from the UI

### 🛠️ Available Tools
1. **Cost Assistant**: AWS pricing and cost optimization
2. **AWS Documentation**: Service information and best practices
3. **Architecture Diagrams**: Visual AWS architecture generation
4. **Migration Planning**: Strategies and recommendations

## Installation

### 1. Install Dependencies

```bash
cd /Users/vasan/2\ Areas/Repo/innovathon/migration_agent
source ../.venv/bin/activate
pip install streamlit pillow
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
streamlit --version
```

## Running the App

### Method 1: Using the Shell Script

```bash
chmod +x run_streamlit.sh
./run_streamlit.sh
```

### Method 2: Direct Command

```bash
streamlit run streamlit_app.py
```

### Method 3: With Custom Port

```bash
streamlit run streamlit_app.py --server.port 8502
```

## Using the Interface

### Main Screen

1. **Chat Input**: Type your questions at the bottom
2. **Sidebar**: Access settings and quick actions
3. **Chat History**: View previous conversations
4. **Diagram Display**: Generated diagrams appear inline

### Example Prompts

**Migration Planning:**
```
Help me migrate a 3-tier web application to AWS
```

**Cost Estimation:**
```
What's the monthly cost for EC2 t3.medium and RDS MySQL in us-east-1?
```

**Architecture Diagrams:**
```
Create an AWS architecture diagram for S3 and CloudFront static website hosting
```

**Service Information:**
```
What is AWS Database Migration Service and how does it work?
```

### Session Management

- **Current Session**: Displayed in sidebar
- **New Session**: Click "🔄 New Session" to start fresh
- **Session History**: Automatically maintained within each session

## Configuration

### Customizing Theme

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF9900"  # AWS Orange
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

### Port Configuration

Default port: 8501

To change:
```bash
streamlit run streamlit_app.py --server.port 8080
```

Or edit `.streamlit/config.toml`:
```toml
[server]
port = 8080
```

## Features in Detail

### 1. Interactive Chat
- Natural language queries
- Conversation context preserved
- Multi-turn conversations supported

### 2. Diagram Generation
- Automatic diagram detection
- Inline display in chat
- Download button for each diagram
- Support for multiple diagrams per query

### 3. Session Persistence
- Session ID tracked automatically
- Conversation history maintained
- Context preserved across queries

### 4. Quick Actions
- Pre-configured example prompts
- One-click query execution
- Common use case templates

## Troubleshooting

### Port Already in Use
```bash
# Use a different port
streamlit run streamlit_app.py --server.port 8502
```

### Import Errors
```bash
# Ensure virtual environment is activated
source ../.venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Diagrams Not Displaying
- Check that `generated-diagrams/` directory exists
- Verify image files are PNG format
- Ensure Pillow is installed: `pip install pillow`

### AWS Credentials
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

## Advanced Usage

### Running in Background

```bash
# Using nohup
nohup streamlit run streamlit_app.py &

# Using screen
screen -S migration-app
streamlit run streamlit_app.py
# Press Ctrl+A, then D to detach
```

### Accessing Remotely

```bash
streamlit run streamlit_app.py --server.address 0.0.0.0
```

Then access at: `http://<your-ip>:8501`

### Development Mode

```bash
# Auto-reload on file changes
streamlit run streamlit_app.py --server.runOnSave true
```

## File Structure

```
migration_agent/
├── streamlit_app.py          # Main Streamlit application
├── migration_agent.py         # Backend agent logic
├── run_streamlit.sh          # Startup script
├── .streamlit/
│   └── config.toml           # Streamlit configuration
├── generated-diagrams/        # Generated diagram storage
└── requirements.txt          # Python dependencies
```

## API Integration

The Streamlit app integrates with:
- **migration_assistant()**: Main entrypoint
- **Cost Assistant**: AWS pricing queries
- **AWS Docs Assistant**: Documentation lookup
- **Architecture Diagram Generator**: Visual diagrams

## Best Practices

1. **Clear Sessions**: Start new session for unrelated queries
2. **Specific Prompts**: Be detailed in architecture requests
3. **Save Diagrams**: Download important diagrams immediately
4. **Check AWS Credentials**: Ensure valid credentials before starting

## Security Notes

- Never commit AWS credentials
- Use IAM roles when possible
- Enable XSRF protection (enabled by default)
- Don't expose to public internet without authentication

## Support

For issues or questions:
1. Check console logs: `streamlit run streamlit_app.py --logger.level debug`
2. Verify AWS credentials: `aws sts get-caller-identity`
3. Test backend directly: `python test_local.py`

## Future Enhancements

- [ ] User authentication
- [ ] Diagram history gallery
- [ ] Export conversation to PDF
- [ ] Multi-language support
- [ ] Cost tracking dashboard
- [ ] Architecture comparison tool
