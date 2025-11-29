# Design Document

## Overview

The AWS Migration Agent System is a multi-agent AI application built on AWS infrastructure that automates the analysis of on-premises applications and generates comprehensive AWS migration proposals. The system leverages AWS Agentic Core for multi-agent orchestration, Amazon Bedrock for AI capabilities, integrates with AWS documentation through MCP (Model Context Protocol), and provides a conversational web interface for user interaction.

**This is designed as a Minimum Viable Product (MVP) for demonstration purposes**, focusing on core functionality with local Streamlit deployment.

### Key Design Principles

1. **MVP-First Approach**: Focus on essential features for demo, avoid over-engineering
2. **Multi-Agent Architecture**: Specialized agents handle distinct responsibilities (document analysis, cost estimation, service recommendations, user interaction, report generation)
3. **Context Persistence**: AWS Agentic Core Memory maintains conversation history and user preferences across sessions
4. **Company-Specific Customization**: ANZ-specific guidelines, VPC configurations, and cost policies are stored in a knowledge base
5. **Conversational Interface**: Natural language interaction through local Streamlit application
6. **Automated Orchestration**: Agent coordination happens automatically through AWS Agentic Core
7. **Simplified Deployment**: Local Streamlit for demo, AWS backend services only

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Chat Interface Layer                      │
│                      (Local Streamlit App)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ AWS SDK / Boto3
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Strands Agent                             │
│              (Deployed in AWS Agentic Core)                      │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Agent Collaboration Layer                    │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │  Design    │  │   Cost     │  │  Service   │         │  │
│  │  │  Analyzer  │  │  Analysis  │  │  Advisor   │         │  │
│  │  │   Agent    │  │   Agent    │  │   Agent    │         │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  │  ┌────────────┐  ┌────────────┐                          │  │
│  │  │   User     │  │   Report   │                          │  │
│  │  │Interaction │  │ Generator  │                          │  │
│  │  │   Agent    │  │   Agent    │                          │  │
│  │  └────────────┘  └────────────┘                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Agentic Core Memory Service                       │  │
│  │    (Customer Memory, Session Context, Preferences)        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌──────────────┐
                    │   Bedrock    │
                    │  Knowledge   │
                    │     Base     │
                    │ (ANZ Docs)   │
                    └──────────────┘
        │
        ▼
┌──────────────┐
│   S3 Bucket  │
│  (Documents, │
│   Reports)   │
└──────────────┘
```

### Technology Stack

- **Programming Language**: Python 3.11+
- **Agent Framework**: AWS Strands Agent (Python) deployed in AWS Agentic Core
- **Foundation Model**: Amazon Bedrock (Claude 3.5 Sonnet or similar)
- **Knowledge Base**: Amazon Bedrock Knowledge Base with OpenSearch Serverless vector store
- **Memory**: AWS Agentic Core Memory Service (built-in customer memory)
- **Document Storage**: Amazon S3
- **Session State**: Managed by AWS Agentic Core
- **Chat Interface**: Local Streamlit application (Python)
- **Agent Communication**: Direct AWS SDK/Boto3 calls from Streamlit to Strands Agent
- **Infrastructure as Code**: Terraform (HCL)
- **Document Processing**: Amazon Textract for PDF/DOCX parsing (via Boto3)
- **Cost Estimation**: AWS Pricing API (via Boto3)
- **PDF Generation**: Python libraries (ReportLab or WeasyPrint)
- **Monitoring**: Amazon CloudWatch

## Components and Interfaces

### 1. Chat Interface Component

**Technology**: Streamlit web application running locally (for MVP demo)

**Responsibilities**:
- Render simple chat interface with message history
- Accept text input from user
- Display agent responses
- Invoke Strands Agent via AWS SDK
- Minimal UI - focus on conversation only

**Key Interfaces**:
```python
class ChatInterface:
    def render_chat_window() -> None
    def handle_user_message(message: str) -> None
    def display_agent_response(response: AgentResponse) -> None
    def invoke_strands_agent(message: str, session_id: str) -> str
```

**Integration Points**:
- Direct Boto3 calls to invoke Strands Agent
- Displays text responses from agent
- No file upload UI, no progress bars, no download buttons
- Agent handles all document processing, visualization generation, and report creation internally

### 2. Streamlit to Strands Agent Communication

**Technology**: Direct AWS SDK (Boto3) calls from Streamlit to AWS Strands Agent

**Responsibilities**:
- Invoke Strands Agent deployed in Agentic Core
- Pass user messages to agent
- Retrieve and display agent text responses

**Key Operations** (using Boto3):
```python
import boto3
import streamlit as st

# Initialize Boto3 client for Bedrock Agent Runtime
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# Invoke Strands Agent via Boto3
response = bedrock_agent_runtime.invoke_agent(
    agentId='agent-id',
    agentAliasId='alias-id',
    sessionId='session-id',
    inputText='user message'
)

# Display response text in chat
st.chat_message("assistant").write(response['output']['text'])
```

**Simplified Approach**:
- Streamlit only handles chat conversation
- All document processing, uploads, analysis, visualization, and report generation handled by Strands Agent
- User provides document paths or S3 URIs via chat messages
- Agent returns text responses with analysis results, recommendations, and S3 URIs for generated reports

**Benefits**:
- Minimal Streamlit code - just chat UI
- All business logic in Strands Agent
- Simpler architecture for MVP
- Reduced latency (direct agent invocation)
- Lower cost (no API Gateway or Lambda charges)
- Easier local development and testing

### 3. AWS Strands Agent in Agentic Core

**Technology**: AWS Strands Agent deployed in AWS Agentic Core with multi-agent collaboration

**Responsibilities**:
- Coordinate multi-agent workflow using Agentic Core
- Route tasks to specialized sub-agents
- Aggregate results from multiple agents
- Maintain workflow state through Agentic Core memory
- Handle error recovery and retries
- Manage customer memory across sessions

**Strands Agent Implementation** (Python 3):
```python
# Strands Agent implemented in Python 3
from aws_strands import Agent, AgentCollaboration

strands_agent = Agent(
    name="MigrationAnalysisAgent",
    description="Multi-agent system for AWS migration analysis",
    foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    instruction="""You are a migration analysis agent that coordinates 
    specialized sub-agents to analyze on-premises applications and generate 
    AWS migration proposals. Use the design analyzer, service advisor, cost 
    analyzer, user interaction, and report generator agents to complete the 
    workflow.""",
    agent_collaboration=AgentCollaboration(
        enabled=True,
        sub_agents=[
            "design_analyzer_agent",
            "service_advisor_agent", 
            "cost_analyzer_agent",
            "user_interaction_agent",
            "report_generator_agent"
        ]
    ),
    memory_configuration={
        "enabled": True,
        "customer_memory_enabled": True,
        "retention_days": 30
    },
    knowledge_bases=["anz_migration_kb"]
)
```

**Note**: All agent code, action groups, and utilities will be implemented in Python 3.

**Sub-Agents**:
Each specialized agent (Design Analyzer, Service Advisor, Cost Analyzer, User Interaction, Report Generator) is configured as a Bedrock Agent that the main Strands Agent can invoke through agent collaboration.

**Workflow State Machine**:
```
INIT → DOCUMENT_UPLOAD → DESIGN_ANALYSIS → SERVICE_RECOMMENDATION →
USER_CLARIFICATION → COST_ANALYSIS → REPORT_GENERATION → COMPLETE
```

**Memory Management**:
- AWS Agentic Core automatically manages customer memory
- Session context persists across conversations
- User preferences and decisions stored in memory service
- Strands Agent maintains workflow state

### 4. Design Analyzer Agent

**Technology**: Amazon Bedrock Agent with document analysis action group

**Responsibilities**:
- Parse HLD and LLD documents using Amazon Textract
- Extract architectural components and relationships
- Identify application tiers (presentation, business logic, data)
- Map on-premises components to AWS service categories
- Detect dependencies and integration points
- Identify potential migration challenges

**Action Group Functions**:
```python
def analyze_hld(document_s3_uri: str) -> Dict:
    """Extract high-level architecture from HLD document"""
    
def analyze_lld(document_s3_uri: str) -> Dict:
    """Extract detailed technical specifications from LLD"""
    
def identify_components() -> List[Component]:
    """List all application components with metadata"""
    
def map_to_aws_categories() -> Dict[str, str]:
    """Map components to AWS service categories"""
    
def detect_dependencies() -> List[Dependency]:
    """Identify component dependencies and integration points"""
```

**Output Schema**:
```json
{
  "components": [
    {
      "name": "Web Server",
      "type": "compute",
      "technology": "Apache Tomcat",
      "specifications": {
        "cpu": "4 cores",
        "memory": "16 GB",
        "storage": "100 GB"
      },
      "dependencies": ["Application Server", "Load Balancer"]
    }
  ],
  "architecture_patterns": ["3-tier", "microservices"],
  "integration_points": [...],
  "migration_challenges": [...]
}
```

### 5. AWS Service Advisor Agent

**Technology**: Amazon Bedrock Agent with MCP integration for AWS documentation

**Responsibilities**:
- Provide AWS service recommendations for each component
- Answer AWS service-specific questions using MCP
- Compare multiple AWS service options
- Rank services based on ANZ preferences
- Explain service capabilities and limitations

**Action Group Functions**:
```python
def recommend_services(component: Component) -> List[ServiceOption]:
    """Recommend AWS services for a component"""
    
def query_aws_docs(query: str) -> str:
    """Query AWS documentation via MCP"""
    
def compare_services(services: List[str]) -> ComparisonMatrix:
    """Compare multiple AWS services"""
    
def get_service_details(service_name: str) -> ServiceDetails:
    """Get detailed information about an AWS service"""
```

**MCP Integration**:
- Uses AWS Documentation MCP server
- Queries service documentation, pricing, best practices
- Retrieves Well-Architected Framework guidance

**Service Recommendation Schema**:
```json
{
  "component": "Web Server",
  "options": [
    {
      "service": "Amazon EC2",
      "instance_type": "t3.xlarge",
      "pros": ["Full control", "Flexible configuration"],
      "cons": ["Requires management", "Higher operational overhead"],
      "estimated_monthly_cost": 120.00,
      "rank": 2
    },
    {
      "service": "AWS Elastic Beanstalk",
      "pros": ["Managed platform", "Auto-scaling", "Easy deployment"],
      "cons": ["Less control", "Platform limitations"],
      "estimated_monthly_cost": 150.00,
      "rank": 1
    }
  ]
}
```

### 6. User Interaction Agent

**Technology**: Amazon Bedrock Agent with conversational capabilities

**Responsibilities**:
- Generate clarifying questions based on analysis gaps
- Collect user preferences and decisions
- Query ANZ knowledge base for company-specific information
- Validate user responses
- Maintain conversational context

**Action Group Functions**:
```python
def generate_clarification_questions(analysis_gaps: List[str]) -> List[Question]:
    """Generate questions to fill analysis gaps"""
    
def collect_user_preference(question: Question) -> Response:
    """Collect and validate user response"""
    
def query_anz_knowledge_base(query: str) -> str:
    """Query ANZ-specific documentation"""
    
def present_service_options(options: List[ServiceOption]) -> Selection:
    """Present options and collect user selection"""
```

**Question Types**:
- Clarification: "What is the expected peak traffic for the web application?"
- Preference: "Do you prefer managed services or more control over infrastructure?"
- Selection: "Which database service would you like to use: RDS, Aurora, or DynamoDB?"
- Validation: "The analysis shows 5 application servers. Is this correct?"

### 7. Cost Analysis Agent

**Technology**: Amazon Bedrock Agent with AWS Pricing API integration

**Responsibilities**:
- Estimate monthly AWS costs for proposed architecture
- Apply ANZ-specific pricing agreements and discounts
- Compare on-premises vs AWS costs
- Identify cost optimization opportunities
- Generate cost breakdown by service

**Action Group Functions**:
```python
def estimate_service_cost(service: str, configuration: Dict) -> float:
    """Estimate cost for a specific AWS service"""
    
def calculate_total_cost(architecture: Architecture) -> CostEstimate:
    """Calculate total monthly cost for architecture"""
    
def apply_anz_discounts(base_cost: float) -> float:
    """Apply ANZ-specific pricing agreements"""
    
def identify_cost_optimizations() -> List[Optimization]:
    """Suggest cost optimization opportunities"""
    
def compare_costs(onprem_cost: float, aws_cost: float) -> Comparison:
    """Compare on-premises vs AWS costs"""
```

**Cost Estimation Schema**:
```json
{
  "total_monthly_cost": 5420.00,
  "breakdown": [
    {
      "service": "Amazon EC2",
      "instances": 3,
      "instance_type": "t3.xlarge",
      "monthly_cost": 360.00
    },
    {
      "service": "Amazon RDS",
      "instance_type": "db.r5.large",
      "monthly_cost": 280.00
    }
  ],
  "optimizations": [
    {
      "recommendation": "Use Reserved Instances for EC2",
      "potential_savings": 720.00
    }
  ],
  "anz_discount_applied": 542.00
}
```

### 8. Report Generator Agent

**Technology**: Amazon Bedrock Agent with PDF generation Lambda function

**Responsibilities**:
- Compile all analysis findings
- Generate structured PDF report
- Include architecture diagrams
- Format cost tables and charts
- Add executive summary

**Action Group Functions**:
```python
def compile_report_data(session_id: str) -> ReportData:
    """Gather all data for report generation"""
    
def generate_architecture_diagram(components: List[Component]) -> Image:
    """Create architecture diagram"""
    
def generate_pdf_report(report_data: ReportData) -> str:
    """Generate PDF and return S3 URI"""
    
def create_executive_summary(report_data: ReportData) -> str:
    """Generate executive summary"""
```

**Report Structure**:
1. Executive Summary
2. Current Architecture Analysis (with architecture diagram)
3. Proposed AWS Architecture (with interactive/static architecture diagram)
4. Service Recommendations
5. Cost Analysis (with cost breakdown charts)
6. Migration Roadmap
7. Risks and Mitigation Strategies
8. Appendices (User Clarifications, ANZ Guidelines Applied)

**Visualization Libraries**:
- **Streamlit UI**: Plotly for interactive charts, Graphviz/Diagrams for architecture visualization
- **PDF Reports**: Matplotlib for static charts, Graphviz for architecture diagrams

### 9. Knowledge Base Component

**Technology**: Amazon Bedrock Knowledge Base with OpenSearch Serverless

**Responsibilities**:
- Store ANZ-specific documentation
- Index documents for semantic search
- Provide retrieval for agent queries
- Support document updates and versioning

**Data Sources**:
- ANZ VPC configuration standards
- ANZ cost optimization policies
- ANZ approved AWS services list
- ANZ security and compliance requirements
- ANZ architecture patterns and templates

**Configuration**:
```python
knowledge_base = {
    "name": "ANZMigrationKnowledgeBase",
    "embedding_model": "amazon.titan-embed-text-v2:0",
    "vector_store": {
        "type": "opensearch_serverless",
        "collection_name": "anz-migration-docs"
    },
    "data_sources": [
        {
            "type": "s3",
            "bucket": "anz-migration-docs",
            "chunking_strategy": {
                "type": "FIXED_SIZE",
                "max_tokens": 300,
                "overlap_percentage": 20
            }
        }
    ]
}
```

### 10. Memory Component

**Technology**: AWS Agentic Core Memory Service (Built-in Customer Memory)

**Responsibilities**:
- Persist conversation history across sessions automatically
- Store user preferences and decisions
- Maintain project context
- Enable context retrieval for resumed sessions
- Provide memory to all agents in the flow

**Memory Configuration**:
```yaml
memory_configuration:
  enabled: true
  customer_memory:
    enabled: true
    retention_days: 30
    max_context_tokens: 4000
  session_memory:
    enabled: true
    retention_days: 7
```

**Stored Context** (Managed by Agentic Core):
- Uploaded document references
- Analysis results
- User responses to clarification questions
- Service selections
- Cost estimates
- Project metadata (name, start date, status)
- Conversation history with semantic understanding

**Key Benefits**:
- No manual memory management required
- Automatic context injection into agent prompts
- Cross-session continuity without custom code
- Built-in memory retrieval and summarization

## Data Models

### Component Model
```python
@dataclass
class Component:
    id: str
    name: str
    type: ComponentType  # COMPUTE, DATABASE, STORAGE, NETWORK, etc.
    technology: str
    specifications: Dict[str, Any]
    dependencies: List[str]
    aws_service_mapping: Optional[str]
    migration_complexity: str  # LOW, MEDIUM, HIGH
```

### ServiceOption Model
```python
@dataclass
class ServiceOption:
    service_name: str
    configuration: Dict[str, Any]
    pros: List[str]
    cons: List[str]
    estimated_monthly_cost: float
    rank: int
    anz_approved: bool
    documentation_links: List[str]
```

### CostEstimate Model
```python
@dataclass
class CostEstimate:
    total_monthly_cost: float
    breakdown: List[ServiceCost]
    optimizations: List[CostOptimization]
    anz_discount_applied: float
    comparison_with_onprem: Optional[CostComparison]
```

### MigrationProject Model
```python
@dataclass
class MigrationProject:
    project_id: str
    session_id: str
    user_id: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentReference]
    components: List[Component]
    service_selections: Dict[str, str]
    cost_estimate: Optional[CostEstimate]
    report_uri: Optional[str]
```

### Session Model
```python
@dataclass
class Session:
    session_id: str
    user_id: str
    project_id: str
    workflow_state: WorkflowState
    created_at: datetime
    last_activity: datetime
    # Note: conversation_history managed by Agentic Core Memory
```

## Error Handling

### Error Categories

1. **Document Processing Errors**
   - Invalid document format
   - Insufficient information in documents
   - Textract extraction failures
   - Mitigation: Provide clear error messages, suggest document improvements

2. **Agent Execution Errors**
   - Agent timeout
   - Invalid agent response
   - Action group function failures
   - Mitigation: Retry logic, fallback to manual input, error logging

3. **Cost Estimation Errors**
   - Pricing API unavailable
   - Missing pricing data for service
   - Mitigation: Use cached pricing data, provide cost ranges

4. **Knowledge Base Errors**
   - Query failures
   - No relevant documents found
   - Mitigation: Fallback to general AWS documentation, notify user

5. **Report Generation Errors**
   - PDF generation failure
   - S3 upload failure
   - Mitigation: Retry, provide alternative formats (HTML, JSON)

### Error Handling Strategy

```python
class ErrorHandler:
    def handle_error(self, error: Exception, context: Dict) -> ErrorResponse:
        """Central error handling with retry logic"""
        
    def retry_with_backoff(self, func: Callable, max_retries: int = 3):
        """Exponential backoff retry"""
        
    def log_error(self, error: Exception, context: Dict):
        """Log to CloudWatch with context"""
        
    def notify_user(self, error: Exception) -> str:
        """Generate user-friendly error message"""
```

## Testing Strategy

### Unit Testing
- Test individual agent action group functions
- Test data model validation
- Test utility functions (cost calculation, document parsing)
- Framework: pytest
- Coverage target: >80%

### Integration Testing
- Test agent-to-agent communication
- Test knowledge base queries
- Test API Gateway endpoints
- Test document upload and processing pipeline
- Framework: pytest with moto for AWS service mocking

### End-to-End Testing
- Test complete migration analysis workflow
- Test multi-session scenarios with memory
- Test error recovery scenarios
- Framework: Selenium for UI testing, pytest for backend

### Performance Testing
- Test concurrent user sessions
- Test large document processing
- Test knowledge base query performance
- Load test API endpoints
- Tools: Locust, AWS CloudWatch metrics

### Security Testing
- Test authentication and authorization
- Test data encryption at rest and in transit
- Test IAM role permissions
- Test input validation and sanitization
- Tools: AWS IAM Access Analyzer, OWASP ZAP

### Test Data
- Sample HLD/LLD documents (PDF format - to be generated for MVP demo)
  - Example: E-commerce application with web tier, app tier, database tier
  - Includes component specifications, dependencies, and architecture diagrams
- Sample ANZ documentation (PDF format)
  - VPC configuration standards
  - Approved AWS services list
  - Cost optimization guidelines
- Mock pricing data
- Expected output reports

## Deployment Architecture

### Infrastructure Components (MVP)

1. **Compute**
   - AWS Strands Agent deployed in AWS Agentic Core
   - Bedrock Agents for specialized sub-agents
   - Local Streamlit application (no containerization for MVP)
   - No Lambda or API Gateway required

2. **Storage**
   - S3 buckets for documents and reports
   - OpenSearch Serverless for knowledge base vectors
   - Agentic Core Memory Service for session and customer memory

3. **Networking** (Simplified for MVP)
   - Direct AWS SDK/Boto3 calls from Streamlit to Strands Agent
   - No API Gateway needed

4. **Security** (Simplified for MVP)
   - IAM roles with least privilege for Strands Agent and Bedrock
   - AWS credentials configured locally for Streamlit (AWS CLI profile)
   - S3 bucket policies for document access

5. **Monitoring** (Basic for MVP)
   - CloudWatch Logs for agent execution
   - Basic CloudWatch Metrics for Bedrock invocations

### Deployment Pipeline

```
Code Repository (GitHub/CodeCommit)
    ↓
AWS CodePipeline
    ↓
├─ Source Stage (Git pull)
├─ Build Stage (terraform plan, run tests)
├─ Deploy Stage (terraform apply to dev)
├─ Test Stage (integration tests)
└─ Deploy Stage (terraform apply to prod with approval)
```

### Environment Strategy (MVP)
- **Demo Environment**: Single region (us-east-1), minimal resources, local Streamlit
- **Future**: Can be extended to staging and production with containerized deployment

## Security Considerations

1. **Data Protection**
   - Encrypt documents in S3 using KMS
   - Encrypt DynamoDB tables
   - Use TLS for all data in transit

2. **Access Control**
   - Cognito for user authentication
   - IAM roles for service-to-service auth
   - Fine-grained permissions for knowledge base access

3. **Compliance**
   - Audit logging to CloudTrail
   - Data retention policies
   - ANZ compliance requirements adherence

4. **Input Validation**
   - Validate all user inputs
   - Sanitize document content
   - Rate limiting on API endpoints

## Scalability Considerations

1. **Horizontal Scaling**
   - Lambda auto-scales by default
   - ECS Fargate with auto-scaling policies
   - OpenSearch Serverless auto-scales

2. **Performance Optimization**
   - Cache frequently accessed knowledge base results
   - Async processing for long-running operations
   - Batch document processing

3. **Cost Optimization**
   - Use Lambda for bursty workloads
   - Reserved capacity for predictable loads
   - S3 lifecycle policies for old documents

## MVP Scope

**In Scope for MVP**:
- Core multi-agent workflow (document analysis → service recommendations → cost analysis → report generation)
- Document processing via agent action groups (PDF format from S3)
- AWS service recommendations with 2-3 options per component
- Simple cost estimation
- PDF report generation with embedded diagrams (handled by agent)
- **Minimal Streamlit chat interface** - text-only conversation, no file uploads, no visualizations in UI
- ANZ knowledge base with sample documents
- Customer memory for single demo session
- **Sample test documents**: Generate sample HLD/LLD PDFs for a simple application (e.g., 3-tier e-commerce app) for demo purposes
- **Visualizations in PDF reports**: Static architecture diagrams and cost charts embedded in generated PDF reports

**Out of Scope for MVP** (Future Enhancements):
- Advanced authentication (Cognito)
- Containerized Streamlit deployment
- Multi-region support
- Advanced error handling and retries
- Comprehensive testing suite
- Production monitoring and alerting
- Multi-cloud support (Azure, GCP)
- Automated migration execution
- Real-time cost tracking
- Integration with JIRA/ServiceNow
- Mobile applications
