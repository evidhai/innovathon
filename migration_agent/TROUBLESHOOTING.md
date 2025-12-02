# Troubleshooting Guide for Migration Agent

## Issue: AWS Credentials Error

### Error Message:
```
InvalidAccessKeyId: The AWS Access Key Id you provided does not exist in our records.
```

### Solution: Refresh AWS Credentials

#### Option 1: Using AWS CLI SSO (Recommended)
```bash
# Login to AWS SSO
aws sso login --profile your-profile-name

# Or if using default profile
aws sso login
```

#### Option 2: Export Temporary Credentials
If you have temporary session credentials from AWS Console:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_SESSION_TOKEN="your-session-token"
```

#### Option 3: Update AWS Credentials File
Edit `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
aws_session_token = YOUR_SESSION_TOKEN  # If using temporary credentials
```

### Verify Credentials Work:

```bash
# Test S3 access
aws s3 ls s3://innovathon-poc-docs-anz/

# Should list files in the bucket
```

---

## Issue: Agent Not Calling input_agent Tool

### Symptoms:
- User asks "analyze appa.jpeg" or "recommend services for hld file"
- Agent responds asking for description instead of calling the tool

### Solution:
The system prompt has been updated to make tool usage mandatory. Ensure:

1. **File name is mentioned in query**:
   - ✓ "Recommend services for appa.jpeg"
   - ✓ "Analyze the hld file diagram.png"
   - ✗ "Analyze the diagram" (no filename)

2. **Test the tool directly**:
```bash
cd migration_agent
python test_s3_access.py
```

3. **Check agent logs** to see if tool is being called:
```bash
# Look for these log messages:
# "input_agent called with query: ..."
# "Extracted filename: ..."
# "Downloading s3://..."
```

---

## Issue: OpenTelemetry Warning

### Warning Message:
```
WARNING:opentelemetry.instrumentation.instrumentor:Attempting to instrument while already instrumented
```

### Impact:
**This is just a warning, not an error.** It happens when OpenTelemetry tries to instrument code that's already been instrumented. The agent will still work correctly.

### To Suppress (Optional):
Add to your code before imports:
```python
import warnings
warnings.filterwarnings("ignore", message="Attempting to instrument while already instrumented")
```

---

## Quick Test Commands

### 1. Test S3 Access
```bash
python migration_agent/test_s3_access.py
```

### 2. Test Agent Locally (Interactive Mode)
```python
from migration_agent import input_agent

# Test the tool directly
result = input_agent("analyze appa.jpeg")
print(result)
```

### 3. Test Full Agent
```bash
cd migration_agent
python agentcore_build.py  # Deploy
python agentcore_launch.py  # Test with payload
```

---

## Common S3 File Issues

### File Not Found:
```json
{
  "status": "error",
  "message": "File 'appa.jpeg' not found in bucket 'innovathon-poc-docs-anz'"
}
```

**Solutions:**
1. List files in bucket: `aws s3 ls s3://innovathon-poc-docs-anz/`
2. Upload file if missing: `aws s3 cp appa.jpeg s3://innovathon-poc-docs-anz/`
3. Check exact filename (case-sensitive): `appa.jpeg` vs `Appa.jpeg`

---

## Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show:
- S3 download progress
- Bedrock API calls
- Tool invocations
- Error stack traces
