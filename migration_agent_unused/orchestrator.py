import base64
import time
import json
import logging
import tempfile
import shutil
import os
from pathlib import Path
from uuid import uuid4
from typing import List, Dict, Any, Optional

import boto3

from mcp import StdioServerParameters, stdio_client
from mcp.server import FastMCP
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# ------------------------------------------------------------------------------------
# Logging & globals
# ------------------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

# Simple in-memory document store (for HLD/LLD, extracted JSON, etc.)
agentcore_memory: Dict[str, Dict[str, Any]] = {}

# Simple in-memory enterprise knowledge fallback
enterprise_knowledge: List[Dict[str, Any]] = []

# Optional OpenSearch integration (Enterprise Knowledge Store)
ENABLE_OPENSEARCH = os.getenv("ENABLE_OPENSEARCH", "false").lower() == "true"
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "migration-knowledge")
opensearch_client = None
if ENABLE_OPENSEARCH:
    try:
        opensearch_client = boto3.client("opensearchserverless")
        logger.info("OpenSearch integration enabled")
    except Exception as e:
        logger.exception("Failed to initialize OpenSearch client, falling back to in-memory store")
        opensearch_client = None

# ------------------------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------------------------

def index_into_knowledge_store(doc: Dict[str, Any]) -> None:
    """
    Store design patterns / extracted structures into enterprise knowledge store.
    If OpenSearch is enabled, index there; otherwise keep in memory.
    """
    global enterprise_knowledge



    if opensearch_client is None:
        enterprise_knowledge.append(doc)
        return

    try:
        # NOTE: This is a placeholder. Adapt to your OpenSearch collection/domain specifics.
        # For example, with an HTTP endpoint you would use 'opensearch-py' instead.
        opensearch_client.batch(
            collectionName=OPENSEARCH_INDEX,
            documents=[json.dumps(doc)]
        )
    except Exception:
        logger.exception("Failed to index document into OpenSearch; storing in memory instead")
        enterprise_knowledge.append(doc)


def query_knowledge_store(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Query enterprise knowledge store for patterns, best practices, mapping rules, etc.
    """
    print ("Retrieving from knowledge store...")
    if opensearch_client is None:
        # Very naive keyword filter on in-memory docs as fallback
        results = []
        for d in enterprise_knowledge:
            text = json.dumps(d).lower()
            if query.lower() in text:
                results.append(d)
            if len(results) >= limit:
                break
        return results

    try:
        # Placeholder example – adapt to your OpenSearch query API
        response = opensearch_client.search(
            collectionName=OPENSEARCH_INDEX,
            queryString=query,
            maxResults=limit,
        )
        hits = response.get("results", [])
        parsed = []
        for h in hits:
            try:
                parsed.append(json.loads(h.get("document", "{}")))
            except json.JSONDecodeError:
                continue
        return parsed
    except Exception:
        logger.exception("Failed to query OpenSearch; falling back to in-memory store")
        return query_knowledge_store(query, limit=limit)


# ------------------------------------------------------------------------------------
# INPUT UNDERSTANDING LAYER
# ------------------------------------------------------------------------------------

@tool
def input_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    INPUT UNDERSTANDING LAYER

    - Accepts HLD/LLD diagrams or text from S3.
    - Uses Nova Vision for OCR/extraction.
    - Uses Titan Text for structuring into JSON.
    - Stores results into agentcore_memory and optionally indexes into the enterprise
      knowledge store (OpenSearch + in-memory fallback).

    Expected payload:
    {
      "bucket": "...",            # S3 bucket with diagrams / docs
      "keys": ["hld.png", ...],   # OR
      "prefix": "hld/",           # (list objects under prefix)
      "user_id": "...",
      "context": {...}
    }
    OR
    {
      "input": "plain text",
      "user_id": "..."
    }
    """
    print("Starting input_agent...")

    user_input = payload.get("input") or payload.get("prompt")

    # Simple echo mode for plain text calls (no S3 ingestion)
    if user_input and not payload.get("bucket"):
        return {
            "status": "success",
            "mode": "echo",
            "text": user_input,
        }

    bucket = payload.get("bucket")
    if not bucket:
        return {
            "status": "error",
            "message": "Missing 'bucket' in payload. Provide 'bucket' + 'keys' or 'prefix'.",
        }

    keys: List[str] = payload.get("keys", [])
    prefix = payload.get("prefix", "")
    user_id = payload.get("user_id", "unknown")
    context = payload.get("context", {})

    nova_model = payload.get("nova_model", "us.amazon.nova-pro-v1:0")
    titan_model = payload.get("titan_model", "us.amazon.titan-text-express-v1:0")

    try:
        s3_client = boto3.client("s3")

        # Discover objects if only prefix is provided
        if prefix and not keys:
            logger.info(f"Listing objects in s3://{bucket}/{prefix}")
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            keys = [obj["Key"] for obj in response.get("Contents", [])]
            logger.info(f"Found {len(keys)} objects under prefix {prefix}")

        if not keys:
            return {
                "status": "error",
                "message": f"No keys found in bucket '{bucket}'. Provide 'keys' or 'prefix'.",
            }

        temp_dir = Path(tempfile.mkdtemp(prefix="hld_lld_"))
        logger.info(f"Using temp dir {temp_dir}")

        results: List[Dict[str, Any]] = []

        # Vision agent (Nova Vision) for OCR / extraction
        vision_agent = Agent(
            model=nova_model,
            system_prompt=(
                "You are an OCR and diagram understanding specialist. "
                "Given an architecture or text image (provided as base64), "
                "extract all text and also summarize key architecture components "
                "and relationships in plain text. Return ONLY text."
            ),
        )

        # Text agent (Titan Text) for structuring into JSON
        text_agent = Agent(
            model=titan_model,
            system_prompt=(
                "You are a structured data specialist. Convert the provided "
                "architecture text into STRICT, valid JSON capturing:\n"
                "- components\n- data stores\n- integrations\n- dependencies\n"
                "- environments (dev/test/prod)\n- non-functional requirements\n"
                "If unsure, make best-effort guesses but keep JSON valid."
            ),
        )

        try:
            for key in keys:
                try:
                    logger.info(f"Processing key: {key}")

                    local_path = temp_dir / key.replace("/", "_")
                    with open(local_path, "wb") as f:
                        s3_client.download_fileobj(bucket, key, f)
                    logger.info(f"Downloaded {key} -> {local_path}")

                    with open(local_path, "rb") as f:
                        image_bytes = f.read()
                    b64_image = base64.b64encode(image_bytes).decode("utf-8")

                    # Step 1: OCR / extraction with Nova Vision
                    vision_prompt = (
                        "Extract all visible text and describe the architecture: \n"
                        f"IMAGE_BASE64:\n{b64_image[:200]}...[truncated]"
                    )
                    vision_response = vision_agent(vision_prompt)
                    try:
                        extracted_text = vision_response.message["content"][0]["text"]
                    except (KeyError, IndexError, TypeError):
                        extracted_text = str(vision_response)

                    logger.info(f"OCR+extracted text length: {len(extracted_text)}")

                    # Step 2: Structure with Titan Text
                    text_prompt = (
                        "Convert the following architecture text into structured JSON:\n\n"
                        f"{extracted_text}"
                    )
                    text_response = text_agent(text_prompt)
                    try:
                        json_text = text_response.message["content"][0]["text"]
                    except (KeyError, IndexError, TypeError):
                        json_text = str(text_response)

                    try:
                        json_data = json.loads(json_text)
                    except json.JSONDecodeError:
                        json_data = {"raw_output": json_text}

                    # Step 3: store in memory
                    memory_id = f"{user_id}_doc_{uuid4().hex[:8]}"
                    memory_entry = {
                        "doc_id": memory_id,
                        "s3_key": key,
                        "user_id": user_id,
                        "timestamp": time.time(),
                        "extracted_text": extracted_text,
                        "json_data": json_data,
                        "context": context,
                    }
                    agentcore_memory[memory_id] = memory_entry
                    logger.info(f"Stored document in memory as {memory_id}")

                    # Step 4: index key structures into enterprise knowledge store
                    index_into_knowledge_store(
                        {
                            "memory_id": memory_id,
                            "s3_key": key,
                            "user_id": user_id,
                            "type": "hld_lld_document",
                            "json_data": json_data,
                            "timestamp": memory_entry["timestamp"],
                        }
                    )

                    results.append(
                        {
                            "key": key,
                            "memory_id": memory_id,
                            "extracted_text": extracted_text,
                            "json_data": json_data,
                        }
                    )

                except Exception as inner_e:
                    logger.exception(f"Error processing key {key}")
                    results.append({"key": key, "error": str(inner_e)})

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return {
            "status": "success",
            "message": f"Processed {len(results)} document(s)",
            "results": results,
            "memory_ids": [r.get("memory_id") for r in results if r.get("memory_id")],
            "memory_location": "agentcore_documents",
        }

    except Exception as e:
        logger.exception("Fatal error in input_agent")
        return {"status": "error", "message": f"Fatal error: {str(e)}"}


# ------------------------------------------------------------------------------------
# ENTERPRISE KNOWLEDGE STORE AGENT
# ------------------------------------------------------------------------------------

@tool
def knowledge_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    ENTERPRISE KNOWLEDGE STORE AGENT

    Uses the Enterprise Knowledge Store (OpenSearch + in-memory) to:
    - Retrieve Cloud Design Patterns
    - AWS Best Practices
    - Compliance Guardrails
    - Service Mapping Rules
    """
    print("Starting knowledge_agent...")
    query = payload.get("query") or payload.get("input") or ""
    if not query:
        return {"status": "error", "message": "Provide 'query' (string) for knowledge_agent"}

    limit = int(payload.get("limit", 5))
    logger.info(f"knowledge_agent query={query}, limit={limit}")

    docs = query_knowledge_store(query=query, limit=limit)
    return {
        "status": "success",
        "query": query,
        "results": docs,
        "source": "opensearch" if opensearch_client else "memory",
    }


# ------------------------------------------------------------------------------------
# PATTERN MATCHING & MIGRATION STRATEGY AGENT
# ------------------------------------------------------------------------------------

@tool
def pattern_matching_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pattern matching and migration strategy suggestion agent.

    Consumes HLD/LLD JSON + optional current stack/constraints, consults the
    knowledge store, and outputs:

    - patterns_identified
    - migration_strategies (6Rs)
    - aws_services_mapping
    - roadmap / risks / guardrails references
    """
    print("Starting pattern_matching_agent...")
    hld_json = payload.get("hld_json")
    lld_json = payload.get("lld_json")
    current_stack = payload.get("current_stack", {})
    constraints = payload.get("constraints", [])
    team_expertise = payload.get("team_expertise", "intermediate")

    # Optional: look up related patterns from the knowledge store
    ks_query = payload.get("knowledge_query", "aws migration patterns")
    knowledge_hits = query_knowledge_store(ks_query, limit=5)

    if not hld_json and not lld_json:
        return {
            "status": "error",
            "message": "Provide 'hld_json' and/or 'lld_json' in payload for pattern_matching_agent",
        }

    try:
        pattern_agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            system_prompt="""You are an expert AWS Migration Architect specializing in pattern recognition
and migration strategy.

You have access to:
- Architecture JSON (HLD/LLD)
- Enterprise knowledge snippets (design patterns, guardrails, mapping rules)

Identify:
1. Architecture patterns (monolith, microservices, event-driven, serverless, data patterns)
2. Best-fit migration strategies per component (6Rs)
3. AWS service mappings
4. Migration roadmap and waves
5. Risk assessment + mitigation linked to guardrails
6. Cost / timeline level estimates

Return STRICT, valid JSON with keys:
- patterns_identified
- migration_strategies
- aws_services_mapping
- roadmap
- risks
- cost_timeline_estimates
""",
        )

        analysis_prompt = {
            "hld_json": hld_json,
            "lld_json": lld_json,
            "current_stack": current_stack,
            "constraints": constraints,
            "team_expertise": team_expertise,
            "knowledge_snippets": knowledge_hits,
        }

        logger.info("Calling pattern_matching_agent LLM for architecture analysis")
        response = pattern_agent(json.dumps(analysis_prompt))

        try:
            analysis_result = response.message["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            analysis_result = str(response)

        try:
            parsed_result = json.loads(analysis_result)
        except json.JSONDecodeError:
            parsed_result = {"raw_analysis": analysis_result}

        # Also index strategy into knowledge store for future reuse
        index_into_knowledge_store(
            {
                "type": "migration_strategy",
                "input": analysis_prompt,
                "analysis": parsed_result,
                "timestamp": time.time(),
            }
        )

        return {
            "status": "success",
            "message": "Pattern matching and strategy analysis complete",
            "analysis": parsed_result,
            "memory_location": "agentcore_migration_strategies",
        }

    except Exception as e:
        logger.exception("Error in pattern_matching_agent")
        return {"status": "error", "message": f"Pattern matching failed: {str(e)}"}


# ------------------------------------------------------------------------------------
# COST & OPTIMIZATION ENGINE
# ------------------------------------------------------------------------------------

@tool
def cost_assistant(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    COST & OPTIMIZATION ENGINE

    Uses the AWS Pricing MCP server + LLM to:
    - Estimate AWS costs for proposed architectures
    - Suggest Savings Plans / RI / rightsizing
    - Compare on-prem vs AWS TCO
    """

    print("Starting cost_assistant...")

    stdio_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command="uvx", args=["awslabs.aws-pricing-mcp-server@latest"])
        )
    )

    logger.info("Initializing cost_assistant with AWS pricing MCP tools")

    with stdio_mcp_client:
        tools = stdio_mcp_client.list_tools_sync()
        logger.info(f"Loaded {len(tools)} pricing tools from MCP server")

        agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            tools=tools,
            system_prompt="""You are an AWS Cost Optimization Assistant.

Use AWS pricing tools to:
- Estimate costs for a proposed target architecture
- Recommend Savings Plans / RIs / rightsizing
- Provide on-prem vs AWS comparison
- Suggest tagging and cost allocation best practices

Return a concise but detailed JSON:
{
  "monthly_cost_estimate": ...,
  "cost_breakdown": {...},
  "savings_recommendations": [...],
  "tco_summary": "...",
  "assumptions": [...]
}
""",
        )

        user_request = payload.get("input") or payload.get("prompt") or json.dumps(payload)
        response = agent(user_request)

        try:
            text = response.message["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            text = str(response)

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = {"raw_cost_analysis": text}

        return {
            "status": "success",
            "cost_analysis": parsed,
        }


# ------------------------------------------------------------------------------------
# TARGET-STATE GENERATION (DIAGRAM + GUARDRAILS + WAVES)
# ------------------------------------------------------------------------------------

@tool
def arch_diag_assistant(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    TARGET-STATE DIAGRAM GENERATION

    Uses the AWS Diagram MCP server + Nova Pro to generate high-level target
    architecture diagrams from:
    - HLD/LLD JSON
    - Migration strategies
    - Knowledge snippets / guardrails
    """

    print("Starting arch_diag_assistant...")

    stdio_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command="uvx", args=["awslabs.aws-diagram-mcp-server@latest"])
        )
    )

    logger.info("Initializing arch_diag_assistant with AWS diagram MCP tools")

    with stdio_mcp_client:
        tools = stdio_mcp_client.list_tools_sync()
        logger.info(f"Loaded {len(tools)} diagram tools from MCP server")

        agent = Agent(
            model="us.amazon.nova-pro-v1:0",
            tools=tools,
            system_prompt="""You are a Senior AWS Solutions Architect specializing in target-state
architecture diagrams for migrations.

Given:
- Source architecture JSON (HLD/LLD)
- Migration strategies and AWS service mappings
- Guardrails and best practices

Generate a target-state architecture diagram specification using AWS iconography.
Show:
- VPCs, subnets, AZs
- Load balancing and networking
- App tiers (web/app/data)
- Managed services (RDS, DynamoDB, Lambda, ECS/EKS, etc.)
- Observability (CloudWatch, CloudTrail, X-Ray)
- Security (IAM, KMS, WAF, SGs, NACLs)

Return JSON with:
{
  "diagram_description": "...",
  "aws_resources": [...],
  "logical_groups": [...],
  "assumptions": [...]
}
""",
        )

        user_request = payload.get("input") or payload.get("prompt") or json.dumps(payload)
        response = agent(user_request)

        try:
            text = response.message["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            text = str(response)

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = {"raw_diagram_spec": text}

        return {
            "status": "success",
            "diagram": parsed,
        }


@tool
def migration_wave_planner(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    MIGRATION WAVE PLANNER

    Takes application inventory / service mappings and groups them into
    migration waves with sequencing, dependencies, and risk levels.
    """
    print("Starting migration_wave_planner...")
    agent = Agent(
        model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        system_prompt="""You are a Migration Wave Planner.

Given:
- Application / component inventory
- Dependencies
- Risk levels and business criticality

Create 2-5 migration waves with:
- wave_name
- scope
- dependencies
- risks
- rollback_strategy

Return STRICT JSON:
{
  "waves": [
     { "name": "...", "scope": [...], "dependencies": [...], "risks": [...], "rollback_strategy": "..." }
  ]
}
""",
    )

    payload_json = json.dumps(payload)
    response = agent(payload_json)

    try:
        text = response.message["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        text = str(response)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"raw_waves": text}

    return {
        "status": "success",
        "waves": parsed,
    }


# ------------------------------------------------------------------------------------
# AWS DOCS HELPER (OPTIONAL, BUT NICE FOR EXPLANATIONS)
# ------------------------------------------------------------------------------------

@tool
def aws_docs_assistant(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    AWS Documentation Assistant – uses AWS docs MCP to answer
    'what is X service' type questions in one-liners.
    """

    print("Asking aws_docs_assistant...")
    stdio_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"])
        )
    )

    logger.info("Initializing aws_docs_assistant with AWS docs MCP tools")

    with stdio_mcp_client:
        tools = stdio_mcp_client.list_tools_sync()
        logger.info(f"Loaded {len(tools)} documentation tools from MCP server")

        agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            tools=tools,
            system_prompt="""You are an AWS Documentation Assistant.

Use docs tools to answer AWS questions in clear one-liners, suitable
for engineers coming from on-prem world.
""",
        )

        user_request = payload.get("input") or payload.get("prompt") or json.dumps(payload)
        response = agent(user_request)

        try:
            text = response.message["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            text = str(response)

        return {
            "status": "success",
            "answer": text,
        }


# ------------------------------------------------------------------------------------
# MIGRATION ORCHESTRATION AGENT (AgentCore Orchestration Engine)
# ------------------------------------------------------------------------------------

migration_system_prompt = """You are an AWS Migration Orchestration Agent sitting behind
AgentCore's orchestration engine.

Your job:
- Take high-level user goals for a cloud migration
- Decide which tools/agents to call (input_agent, knowledge_agent,
  pattern_matching_agent, cost_assistant, arch_diag_assistant,
  migration_wave_planner, aws_docs_assistant)
- Compose a full migration plan.

When appropriate:
1. Use input_agent to ingest HLD/LLD diagrams and get JSON and memory_ids.
2. Use knowledge_agent to pull patterns, best practices, guardrails.
3. Use pattern_matching_agent to identify patterns and migration strategies.
4. Use arch_diag_assistant to generate target-state architecture diagrams.
5. Use cost_assistant to estimate cost and optimizations.
6. Use migration_wave_planner to group workloads into migration waves.
7. Summarize everything into 'Migration Outputs':
   - migration_strategy
   - target_state_diagram_summary
   - aws_resource_mapping
   - risks_and_mitigation
   - cost_estimation
   - migration_waves
Always return a final user-facing explanation plus a structured JSON summary.
"""

migration_agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt=migration_system_prompt,
    tools=[
        input_agent,
        knowledge_agent,
        pattern_matching_agent,
        cost_assistant,
        aws_docs_assistant,
        arch_diag_assistant,
        migration_wave_planner,
    ],
)


# ------------------------------------------------------------------------------------
# AgentCore entrypoint
# ------------------------------------------------------------------------------------

@app.entrypoint
def migration_assistant(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    AgentCore entrypoint for the multi-agent AWS migration assistant.

    Expected payload:
    {
      "input": "User question or instruction",
      "user_id": "optional",
      "context": {...}
    }
    """

    user_input = payload.get("input") or payload.get("prompt") or ""
    user_id = payload.get("user_id", "unknown")
    context = payload.get("context", {})

    logger.info(f"[migration_assistant] user_id={user_id}, input={user_input!r}")
    if context:
        logger.info(f"[migration_assistant] context={context}")

    response = migration_agent(user_input)

    try:
        answer_text = response.message["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        answer_text = str(response)

    return {
        "status": "success",
        "user_id": user_id,
        "answer": answer_text,
        "context": context,
    }


if __name__ == "__main__":
    app.run()
