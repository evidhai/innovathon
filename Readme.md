Commands to setup your environemnt

```
python -m venv .venv

And activate the virtual environment:

    macOS / Linux: source .venv/bin/activate
    Windows (CMD): .venv\Scripts\activate.bat
    Windows (PowerShell): .venv\Scripts\Activate.ps1


pip install strands-agents-tools strands-agents-builder

```

```
pip install "bedrock-agentcore-starter-toolkit>=0.1.21" strands-agents strands-agents-tools boto3
```

## Run:

- First update agent code in main_v1.py
- Run agentcore_build.py to create equivalent docker file and launch the agentcore
- Test with a prompt by running agentcore_launch.py
- To destroy runtime, uncomment section of cleanup and run agentcore_build.py