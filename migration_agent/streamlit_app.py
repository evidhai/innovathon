"""
Streamlit UI for AWS Migration Agent
"""
import streamlit as st
import json
import time
import sys
import os
import threading
from pathlib import Path
from queue import Queue, Empty

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from migration_agent import migration_assistant
from PIL import Image

# Use absolute path for diagram directory
DIAGRAM_DIR = Path(__file__).parent / "generated-diagrams"
HISTORY_DIR = Path(__file__).parent / "chat_histories"
HISTORY_DIR.mkdir(exist_ok=True)

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
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main container styling */
    .main {
        background-color: #f8f9fa;
        color: #1e1e1e;
    }

    /* Primary text and headers */
    h1, h2, h3 {
        color: #232f3e; /* AWS Dark Blue */
        font-weight: 700;
    }
    
    h1 {
        margin-bottom: 0.5rem;
    }

    /* Subheader styling */
    .subheader {
        color: #d13212; /* AWS Orange accent */
        font-weight: 600;
        margin-top: 1.5rem;
    }

    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: none;
    }

    /* Primary Buttons (simulated via CSS targeting generic classes if specific isn't available, 
       but Streamlit's primaryColor handles the main action buttons usually. 
       We'll add hover effects) */
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #232f3e; /* AWS Dark Blue */
        border-right: 1px solid #1a232e;
    }
    
    /* Force white text for all sidebar elements */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] div[data-testid="stMetricValue"],
    [data-testid="stSidebar"] div[data-testid="stMetricLabel"],
    [data-testid="stSidebar"] summary,
    [data-testid="stSidebar"] summary > div,
    [data-testid="stSidebar"] summary span,
    [data-testid="stSidebar"] summary svg {
        color: #ffffff !important;
        fill: #ffffff !important; /* For SVGs in expander */
    }
    
    /* Fix background of expander to be transparent so white text shows */
    [data-testid="stSidebar"] details {
        background-color: transparent !important;
        border-color: rgba(255,255,255,0.2) !important;
    }
    
    [data-testid="stSidebar"] summary {
        background-color: transparent !important;
    }
    
    [data-testid="stSidebar"] summary:hover {
        background-color: rgba(255,255,255,0.1) !important;
        color: #ffffff !important;
    }
    
    /* Input fields in sidebar - keep text dark on white background */
    [data-testid="stSidebar"] input {
        color: #232f3e !important;
    }
    
    /* Buttons in Sidebar - Make them distinct */
    [data-testid="stSidebar"] .stButton button {
        background-color: #f0f2f6;
        color: #232f3e !important; /* Dark text for contrast on light button */
        border: none;
    }
    
    [data-testid="stSidebar"] .stButton button p {
        color: #232f3e !important;
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #ffffff;
    }

    /* Diagram Container */
    .diagram-container {
        border: 1px solid #e1e4e8;
        border-radius: 12px;
        padding: 1.5rem;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin: 1.5rem 0;
    }

    /* Chat Message Styling */
    .stChatMessage {
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    div[data-testid="stChatMessageContent"] {
        background-color: transparent;
    }

    /* User Message Background */
    div[data-testid="chatAvatarIcon-user"] {
        background-color: #f0f2f6;
    }

    /* Assistant Message Background */
    div[data-testid="chatAvatarIcon-assistant"] {
        background-color: #ff9900; /* AWS Orange */
    }
    
    /* Footer Styling */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #ffffff;
        color: #666; 
        text-align: center;
        padding: 1rem 0; 
        font-size: 0.85rem;
        border-top: 1px solid #eee;
        z-index: 1000;
    }
    
    /* Ensure content isn't hidden behind footer */
    .block-container {
        padding-bottom: 5rem;
    }
    
    /* Adjust chat input position to not be hidden by footer */
    [data-testid="stBottom"] {
        bottom: 4rem;
        background-color: transparent;
    }

    /* Floating attachment button - Target the popover container directly */
    /* We exclude sidebar popovers if any exist, ensuring we only target the main chat one */
    [data-testid="stAppViewContainer"] > .main [data-testid="stPopover"] {
        position: fixed;
        bottom: 4.5rem; /* Just above the chat input padding */
        left: 2rem; /* Initial left position */
        z-index: 1000;
        width: auto;
    }
    
    /* Style the button inside to look circular/icon-like if needed, 
       but standard button is fine. Adjust left position for wider screens? 
       Streamlit centers content, so fixed left:2rem might look odd on wide screens.
       Better to try to align with center. But 'left: 2rem' ensures it's accessible.
    */

    /* Attachment status pill */
    .attachment-pill {
        display: inline-flex;
        align-items: center;
        background-color: #e6f3ff;
        color: #0073bb;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        border: 1px solid #0073bb;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

def load_history(session_id):
    history_file = HISTORY_DIR / f"{session_id}.json"
    if history_file.exists():
        try:
            with open(history_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
    return []

def save_history(session_id, history):
    history_file = HISTORY_DIR / f"{session_id}.json"
    try:
        with open(history_file, "w") as f:
            json.dump(history, f)
    except Exception as e:
        print(f"Error saving history: {e}")

# Initialize session state

# Check for session_id in query params
if "session_id" in st.query_params:
    session_id = st.query_params["session_id"]
    if 'session_id' not in st.session_state or st.session_state.session_id != session_id:
        st.session_state.session_id = session_id
        st.session_state.chat_history = load_history(session_id)
elif 'session_id' not in st.session_state:
    new_id = f"session_{int(time.time())}"
    st.session_state.session_id = new_id
    st.session_state.chat_history = []
    st.query_params["session_id"] = new_id

if 'chat_history' not in st.session_state:
     st.session_state.chat_history = []
if 'known_diagrams' not in st.session_state:
    if DIAGRAM_DIR.exists():
        st.session_state.known_diagrams = set(str(f) for f in DIAGRAM_DIR.glob("*.png"))
    else:
        st.session_state.known_diagrams = set()
if 'stop_processing' not in st.session_state:
    st.session_state.stop_processing = False

# Sidebar

with st.sidebar:
    st.title("⚙️ Settings")
    
    with st.expander("👤 User Profile", expanded=True):
        user_id = st.text_input("User ID", value="streamlit_user")
    
    st.divider()
    
    st.subheader("Session Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New", help="Start a new session"):
            st.session_state.chat_history = []
            new_id = f"session_{int(time.time())}"
            st.session_state.session_id = new_id
            st.query_params["session_id"] = new_id
            # Reset known diagrams to current files so we don't show old ones
            if DIAGRAM_DIR.exists():
                st.session_state.known_diagrams = set(str(f) for f in DIAGRAM_DIR.glob("*.png"))
            else:
                st.session_state.known_diagrams = set()
            st.session_state.uploader_key += 1 # Reset uploader
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", help="Refresh/Clear Diagram Cache"):
            st.session_state.known_diagrams = set()
            st.rerun()
            
    st.caption(f"Session ID: `{st.session_state.session_id}`")
    
    st.divider()
    
    # Diagram status
    st.subheader("📊 Diagrams")
    if DIAGRAM_DIR.exists():
        all_pngs = list(DIAGRAM_DIR.glob("*.png"))
        st.metric("Generated Diagrams", len(all_pngs))
    else:
        st.warning("Diagram directory not found")
    
    st.divider()
    
    st.subheader("🚀 Sample Prompts")
    example_prompts = {
        "Simple Migration": "Help me migrate a 3-tier web application from on-premises to AWS",
        "Cost Estimate": "What's the monthly cost for running EC2 t3.medium and RDS MySQL db.t3.medium in us-east-1?",
        "Architecture Diagram": "Create an AWS architecture diagram for a serverless web application using S3, CloudFront, API Gateway, and Lambda",
        "AWS Service Info": "Explain AWS Database Migration Service and how it helps with migrations",
        "VPC Subnet Calculator": "Calculate the number of subnets needed for a VPC with a CIDR block of 10.0.0.0/16 and 3 Availability Zones",
    }
    
    for label, prompt in example_prompts.items():
        if st.button(label, use_container_width=True):
            st.session_state.current_prompt = prompt

# Main content
st.title("☁️ AWS Migration Assistant")
st.markdown("### Your intelligent companion for AWS cloud migration")

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

# Initialize uploader key for resetting
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# Chat Input Area with Attachment
# Floating popover handled by CSS
with st.popover("📎", help="Attach Architecture Diagram (HLD/LLD)"):
    uploaded_file = st.file_uploader(
        "Upload architecture diagram", 
        type=['png', 'jpg', 'jpeg'],
        key=f"uploader_{st.session_state.uploader_key}"
    )

# Status pill for attached file
if uploaded_file:
    st.markdown(f"""
        <div style="position: fixed; bottom: 7rem; left: 2rem; z-index: 1000;">
            <span class="attachment-pill">
                📎 Attached: {uploaded_file.name}
            </span>
        </div>
    """, unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Ask about AWS migration, costs, architecture, or services...")


# Handle example prompt from sidebar
if 'current_prompt' in st.session_state and st.session_state.current_prompt:
    user_input = st.session_state.current_prompt
    del st.session_state.current_prompt

if user_input:
    # Reset stop flag
    st.session_state.stop_processing = False
    
    # Process attached image if any
    image_payload = {}
    user_display_content = user_input
    
    if uploaded_file:
        import base64
        # Convert to base64
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        image_format = uploaded_file.type.split('/')[-1]
        
        image_payload = {
            "image_data": base64_image,
            "image_base64": base64_image, # Redundant but safe
            "image_format": image_format
        }
        
        # Add note to display
        user_display_content += f"\n\n*📎 [Attached Image: {uploaded_file.name}]*"
    
    # Add user message to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_display_content
    })
    save_history(st.session_state.session_id, st.session_state.chat_history)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_display_content)
        if uploaded_file:
            st.image(uploaded_file, width=300)
    
    # Display assistant response
    with st.chat_message("assistant", avatar="☁️"):
        response_placeholder = st.empty()
        status_container = st.container()
        
        try:
            # Show status updates
            with status_container:
                status = st.status("Processing your request...", expanded=True)
                status.write("🔧 Initializing migration assistant...")
                if uploaded_file:
                    status.write("🖼️ Uploading and analyzing architecture diagram...")
            
            # Prepare payload matching migration_agent.py's expected structure
            payload = {
                "input": user_input,
                "user_id": user_id,
                "context": {
                    "session_id": st.session_state.session_id
                }
            }
            
            # Merge image data if present
            if image_payload:
                payload.update(image_payload)
            
            # Increment uploader key to clear it for next turn
            if uploaded_file:
                st.session_state.uploader_key += 1
            
            with status_container:
                status.write("💭 Analyzing your request...")
            
            # Run migration assistant in a separate thread with timeout capability
            result_queue = Queue()
            exception_queue = Queue()
            
            def run_assistant():
                try:
                    # Run async function in new event loop
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(migration_assistant(payload))
                    loop.close()
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)
            
            # Start the thread
            assistant_thread = threading.Thread(target=run_assistant, daemon=True)
            assistant_thread.start()
            
            # Add stop button that actually works
            stop_button_placeholder = st.empty()
            response = None
            timeout = 300  # 5 minutes timeout
            start_time = time.time()
            poll_count = 0
            
            # Poll for results with stop button
            while assistant_thread.is_alive():
                poll_count += 1
                # Check if stop button is pressed
                with stop_button_placeholder.container():
                    if st.button("⏹️ Stop Processing", key=f"stop_btn_{st.session_state.session_id}_{poll_count}", type="secondary"):
                        st.session_state.stop_processing = True
                        with status_container:
                            status.update(label="Stopping...", state="error")
                        # Thread will continue but we'll abandon it
                        raise InterruptedError("Processing stopped by user")
                
                # Check timeout
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Processing timed out after {timeout} seconds")
                
                # Check if result is ready
                try:
                    response = result_queue.get(timeout=0.1)
                    break
                except Empty:
                    pass
                
                # Check if exception occurred
                try:
                    exc = exception_queue.get_nowait()
                    raise exc
                except Empty:
                    pass
                
                time.sleep(0.1)
            
            # Clear stop button
            stop_button_placeholder.empty()
            
            # Get result if thread finished
            if response is None and not exception_queue.empty():
                raise exception_queue.get()
            elif response is None and not result_queue.empty():
                response = result_queue.get()
            elif response is None:
                raise RuntimeError("No response received from assistant")
            
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
                
                # Update diagrams list for this message
                diagrams = [str(f) for f in recent_diagrams]
                
                # Update known diagrams set
                for f in all_diagrams:
                    st.session_state.known_diagrams.add(str(f))
                
                if diagrams:
                    st.divider()
                    st.subheader("📊 Generated Architecture Diagrams")
                    
                    # Display diagrams
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
                                                key=f"new_download_{st.session_state.session_id}_{Path(diagram_path).name}",
                                                use_container_width=True
                                            )
                                except Exception as e:
                                    st.error(f"Error displaying image: {e}")
            # Add assistant message to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response_text,
                "diagrams": diagrams
            })
            save_history(st.session_state.session_id, st.session_state.chat_history)
        
        except InterruptedError:
            with status_container:
                status.update(label="Stopped by user", state="error", expanded=False)
            
            error_msg = "⚠️ **Processing Stopped**\n\nYou stopped the processing. The backend thread will complete in the background."
            response_placeholder.warning(error_msg)
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_msg,
                "diagrams": []
            })
            save_history(st.session_state.session_id, st.session_state.chat_history)
        
        except TimeoutError as e:
            with status_container:
                status.update(label="Timeout", state="error", expanded=False)
            
            error_msg = f"⏱️ **Timeout**\n\n{str(e)}"
            response_placeholder.error(error_msg)
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_msg,
                "diagrams": []
            })
            save_history(st.session_state.session_id, st.session_state.chat_history)
            
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
            save_history(st.session_state.session_id, st.session_state.chat_history)
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

# Footer after input
st.divider()


st.markdown("""
    <div class='footer'>
        AWS Migration Assistant | Powered by Amazon Bedrock & Claude <br>
        <small>© 2025 IBM Innovathon</small>
    </div>
    """, unsafe_allow_html=True)