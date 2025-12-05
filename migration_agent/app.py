"""
Streamlit UI for AWS Migration Agent
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

from migration_agent import migration_assistant
from PIL import Image

# Use absolute path for diagram directory
DIAGRAM_DIR = Path(__file__).parent / "generated-diagrams"

# Page configuration
st.set_page_config(
    page_title="AWS Migration Assistant",
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
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if 'known_diagrams' not in st.session_state:
    st.session_state.known_diagrams = set()
if 'stop_processing' not in st.session_state:
    st.session_state.stop_processing = False

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    st.subheader("User Information")
    user_id = st.text_input("User ID", value="streamlit_user")
    
    st.subheader("Session Info")
    st.info(f"Session ID: {st.session_state.session_id}")
    
    if st.button("🔄 New Session"):
        st.session_state.chat_history = []
        st.session_state.session_id = f"session_{int(time.time())}"
        st.session_state.known_diagrams = set()  # Clear known diagrams
        st.rerun()
    
    if st.button("🔍 Refresh Diagrams"):
        st.session_state.known_diagrams = set()  # Clear to re-detect all diagrams
        st.info("Diagrams cache cleared! Send a new message to see all diagrams.")
    
    st.divider()
    
    # Diagram status
    st.subheader("📊 Diagram Status")
    if DIAGRAM_DIR.exists():
        all_pngs = list(DIAGRAM_DIR.glob("*.png"))
        st.metric("Total Diagrams", len(all_pngs))
        if all_pngs:
            latest = max(all_pngs, key=lambda x: x.stat().st_mtime)
            st.caption(f"Latest: {latest.name}")
    else:
        st.warning("Diagram directory not found")
    
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
st.title("☁️ AWS Migration Assistant")
st.markdown("### Your intelligent companion for AWS cloud migration")

# Image upload section
st.subheader("📋 HLD/LLD Image Analysis")
uploaded_file = st.file_uploader(
    "Upload your High Level Design (HLD) or Low Level Design (LLD) diagram",
    type=['png', 'jpg', 'jpeg'],
    help="Upload architecture diagrams for AI-powered analysis and migration planning"
)

# Initialize session state for uploaded image
if 'uploaded_image_data' not in st.session_state:
    st.session_state.uploaded_image_data = None
if 'uploaded_image_format' not in st.session_state:
    st.session_state.uploaded_image_format = None

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
            
            # Display any generated diagrams
            if "diagrams" in message and message["diagrams"]:
                st.divider()
                st.subheader("📊 Architecture Diagrams")
                
                # Display in columns (max 2 per row) - only diagrams from this message
                diagrams = message["diagrams"]
                for idx in range(0, len(diagrams), 2):
                    cols = st.columns(2)
                    for col_idx, diagram_path in enumerate(diagrams[idx:idx+2]):
                        with cols[col_idx]:
                            try:
                                if Path(diagram_path).exists():
                                    img = Image.open(diagram_path)
                                    st.image(img, caption=Path(diagram_path).name, use_container_width=True)
                                    
                                    with open(diagram_path, "rb") as f:
                                        st.download_button(
                                            label="⬇️ Download PNG",
                                            data=f,
                                            file_name=Path(diagram_path).name,
                                            mime="image/png",
                                            key=f"history_download_{i}_{idx}_{col_idx}",
                                            use_container_width=True
                                        )
                                else:
                                    st.warning(f"Diagram file not found: {Path(diagram_path).name}")
                            except Exception as e:
                                st.error(f"Error loading image: {e}")

# Handle example prompt from sidebar
if 'current_prompt' in st.session_state and st.session_state.current_prompt:
    user_input = st.session_state.current_prompt
    del st.session_state.current_prompt

if user_input:
    # Reset stop flag
    st.session_state.stop_processing = False
    
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
        stop_button_container = st.container()
        
        # Add stop button
        with stop_button_container:
            if st.button("⏹️ Stop Processing", key="stop_btn", type="secondary"):
                st.session_state.stop_processing = True
                st.warning("⚠️ Stop requested - processing will terminate...")
        
        try:
            # Check stop flag before starting
            if st.session_state.stop_processing:
                response_placeholder.warning("Processing stopped by user")
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "⚠️ Processing stopped by user",
                    "diagrams": []
                })
                st.stop()
            
            # Show status updates
            with status_container:
                status = st.status("Processing your request...", expanded=True)
                status.write("🔧 Initializing migration assistant...")
            
            # Check stop flag
            if st.session_state.stop_processing:
                status.update(label="Stopped by user", state="error")
                raise InterruptedError("Processing stopped by user")
            
            # Prepare payload matching migration_agent.py's expected structure
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
                if st.session_state.uploaded_image_data and ('analyze' in user_input.lower() or 'hld' in user_input.lower() or 'lld' in user_input.lower() or getattr(st.session_state, 'analyze_image', False)):
                    status.write("🖼️ Step 1: Analyzing HLD/LLD diagram with Nova Vision...")
                    status.write("💰 Step 2: Gathering cost analysis and optimization...")
                    status.write("📚 Step 3: Collecting AWS best practices and documentation...")
                    status.write("📝 Step 4: Generating comprehensive migration strategy...")
                else:
                    status.write("💭 Analyzing your request...")
            
            # Check stop flag before API call
            if st.session_state.stop_processing:
                status.update(label="Stopped by user", state="error")
                raise InterruptedError("Processing stopped by user")
            
            # Get response from migration assistant
            response = migration_assistant(payload)
            
            # Parse response - handle both string and structured responses
            if isinstance(response, dict):
                response_text = response.get('message', {}).get('content', [{}])[0].get('text', str(response))
            else:
                response_text = str(response)
            
            with status_container:
                status.write("✅ Response ready!")
                status.update(label="Complete!", state="complete", expanded=False)
            
            # Display response
            response_placeholder.markdown(response_text)
            
            # Check for generated diagrams
            diagrams = []
            if DIAGRAM_DIR.exists():
                # Get all PNG diagrams
                all_diagrams = sorted(
                    DIAGRAM_DIR.glob("*.png"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                
                # Find newly generated diagrams (not in known set)
                recent_diagrams = [
                    f for f in all_diagrams
                    if str(f) not in st.session_state.known_diagrams
                ]
                
                # Update known diagrams set
                for f in all_diagrams:
                    st.session_state.known_diagrams.add(str(f))
                
                if recent_diagrams:
                    st.divider()
                    st.subheader("📊 Generated Architecture Diagrams")
                    st.caption(f"Found {len(recent_diagrams)} new diagram(s) for this request")
                    
                    # Display diagrams in columns (max 2 per row)
                    for idx in range(0, len(recent_diagrams), 2):
                        cols = st.columns(2)
                        for col_idx, diagram_path in enumerate(recent_diagrams[idx:idx+2]):
                            with cols[col_idx]:
                                try:
                                    img = Image.open(diagram_path)
                                    st.image(img, caption=diagram_path.name, use_container_width=True)
                                    
                                    with open(diagram_path, "rb") as f:
                                        st.download_button(
                                            label="⬇️ Download PNG",
                                            data=f,
                                            file_name=diagram_path.name,
                                            mime="image/png",
                                            key=f"download_latest_{int(time.time())}_{idx}_{col_idx}",
                                            use_container_width=True
                                        )
                                    diagrams.append(str(diagram_path))
                                except Exception as e:
                                    st.error(f"Error loading image {diagram_path.name}: {e}")
                else:
                    # Debug: Show why no diagrams were found
                    with st.expander("🔍 Diagram Debug Info"):
                        st.write(f"Total PNG files: {len(all_diagrams)}")
                        st.write(f"Known diagrams: {len(st.session_state.known_diagrams)}")
                        if all_diagrams:
                            st.write("Recent files:")
                            for f in all_diagrams[:5]:
                                st.code(f"{f.name} - {time.ctime(f.stat().st_mtime)}")
            
            # Add assistant message to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response_text,
                "diagrams": diagrams
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
                "content": error_msg,
                "diagrams": []
            })

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <small>AWS Migration Assistant | Powered by Amazon Bedrock & Claude</small>
    </div>
    """, unsafe_allow_html=True)
