"""
Demo Streamlit UI for AWS Migration Agent (No AWS credentials required)
"""
import streamlit as st
import json
import time
import sys
import os
import base64
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from migration_agent_demo import migration_assistant_demo
from PIL import Image

# Use absolute path for diagram directory
DIAGRAM_DIR = Path(__file__).parent / "generated-diagrams"

# Page configuration
st.set_page_config(
    page_title="AWS Migration Assistant (Demo)",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .diagram-container {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .demo-banner {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Demo banner
st.markdown("""
    <div class="demo-banner">
        <strong>🚀 DEMO MODE</strong> - This is a demonstration version that works without AWS credentials. 
        All responses are simulated for testing purposes.
    </div>
    """, unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"demo_session_{int(time.time())}"
if 'uploaded_image_data' not in st.session_state:
    st.session_state.uploaded_image_data = None
if 'uploaded_image_format' not in st.session_state:
    st.session_state.uploaded_image_format = None

# Sidebar
with st.sidebar:
    st.title("⚙️ Demo Settings")
    
    st.subheader("User Information")
    user_id = st.text_input("User ID", value="demo_user")
    
    st.subheader("Session Info")
    st.info(f"Session ID: {st.session_state.session_id}")
    
    if st.button("🔄 New Session"):
        st.session_state.chat_history = []
        st.session_state.session_id = f"demo_session_{int(time.time())}"
        st.rerun()
    
    st.divider()
    
    st.subheader("Quick Actions")
    example_prompts = {
        "🚀 Simple Migration": "Help me migrate a 3-tier web application from on-premises to AWS",
        "💰 Cost Estimate": "What's the monthly cost for running EC2 t3.medium and RDS MySQL db.t3.medium in us-east-1?",
        "📊 Architecture Diagram": "Create an AWS architecture diagram for a serverless web application using S3, CloudFront, API Gateway, and Lambda",
        "📚 AWS Service Info": "Explain AWS Database Migration Service and how it helps with migrations",
        "🏗️ Migration Strategy": "What are the best practices for migrating a monolithic application to microservices on AWS?",
        "🖼️ HLD/LLD Analysis": "Upload your High Level Design or Low Level Design diagram for analysis",
    }
    
    for label, prompt in example_prompts.items():
        if st.button(label):
            st.session_state.current_prompt = prompt

# Main content
st.title("☁️ AWS Migration Assistant (Demo)")
st.markdown("### Your intelligent companion for AWS cloud migration")

# Image upload section
st.subheader("📋 HLD/LLD Image Analysis")
uploaded_file = st.file_uploader(
    "Upload your High Level Design (HLD) or Low Level Design (LLD) diagram",
    type=['png', 'jpg', 'jpeg'],
    help="Upload architecture diagrams for AI-powered analysis and migration planning"
)

# Process uploaded image
if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption=f"Uploaded: {uploaded_file.name}", use_container_width=True)
    
    # Convert to base64 for processing
    import io
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Store in session state
    st.session_state.uploaded_image_data = base64.b64encode(img_buffer.getvalue()).decode()
    st.session_state.uploaded_image_format = "png"
    
    # Add analyze button
    if st.button("🔍 Analyze HLD/LLD Diagram", type="primary"):
        st.session_state.current_prompt = "Analyze the uploaded HLD/LLD diagram for AWS migration planning"
        st.session_state.analyze_image = True

# Chat input
user_input = st.chat_input("Ask about AWS migration, costs, architecture, or services...")

# Display chat history
for i, message in enumerate(st.session_state.chat_history):
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    else:
        with st.chat_message("assistant", avatar="☁️"):
            st.markdown(message["content"])

# Handle example prompt from sidebar
if 'current_prompt' in st.session_state and st.session_state.current_prompt:
    user_input = st.session_state.current_prompt
    del st.session_state.current_prompt

if user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Display assistant response
    with st.chat_message("assistant", avatar="☁️"):
        response_placeholder = st.empty()
        status_container = st.container()
        
        try:
            # Show status updates
            with status_container:
                status = st.status("Processing your request...", expanded=True)
                if st.session_state.uploaded_image_data and ('analyze' in user_input.lower() or 'hld' in user_input.lower() or 'lld' in user_input.lower() or getattr(st.session_state, 'analyze_image', False)):
                    status.write("🖼️ Analyzing HLD/LLD diagram (Demo Mode)...")
                    status.write("📝 Generating structured output (Demo Mode)...")
                else:
                    status.write("💭 Analyzing your request (Demo Mode)...")
            
            # Prepare payload
            payload = {
                "input": user_input,
                "user_id": user_id,
                "context": {
                    "session_id": st.session_state.session_id
                }
            }
            
            # Add image data if available and user is analyzing image
            if (st.session_state.uploaded_image_data and 
                ('analyze' in user_input.lower() or 'hld' in user_input.lower() or 'lld' in user_input.lower() or
                 getattr(st.session_state, 'analyze_image', False))):
                payload["image_data"] = st.session_state.uploaded_image_data
                payload["image_format"] = st.session_state.uploaded_image_format
                # Clear the analyze flag
                if hasattr(st.session_state, 'analyze_image'):
                    del st.session_state.analyze_image
            
            with status_container:
                status.write("✅ Response ready!")
                status.update(label="Complete!", state="complete", expanded=False)
            
            # Get response from demo migration assistant
            response = migration_assistant_demo(payload)
            
            # Display response
            response_placeholder.markdown(response)
            
            # Add assistant message to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            
            with status_container:
                status.update(label="Error occurred", state="error", expanded=True)
                status.write(f"❌ {str(e)}")
            
            error_msg = f"**Error Processing Request**\n\n{str(e)}"
            
            # Show detailed error in expander
            with st.expander("🔍 View Error Details"):
                st.code(error_detail, language="python")
            
            response_placeholder.error(error_msg)
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_msg
            })

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <small>AWS Migration Assistant (Demo Mode) | Simulated responses for testing</small>
    </div>
    """, unsafe_allow_html=True)