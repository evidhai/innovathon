"""
Simple architecture diagram generator using Amazon Titan Image Generator
This bypasses the MCP complexity and directly generates diagrams
"""

import base64
import boto3
import json
import time
from pathlib import Path
from uuid import uuid4

DIAGRAM_OUTPUT_DIR = Path("generated-diagrams")
DIAGRAM_OUTPUT_DIR.mkdir(exist_ok=True)

def generate_architecture_diagram(user_request):
    """
    Generate an AWS architecture diagram using Titan Image Generator
    
    Args:
        user_request: User's description of the architecture needed
        
    Returns:
        Path to the generated diagram image
    """
    bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Step 1: Use Claude to create a detailed visual description
    description_prompt = f"""You are an AWS Solutions Architect. Based on this request: "{user_request}"

Create a detailed, visual description for an AWS architecture diagram image that includes:
1. Specific AWS service icons and their exact placement (left/right/center, top/bottom)
2. Visual connections and data flow arrows between services
3. Color-coded security boundaries and VPC layouts
4. Clear labels for each component
5. Network topology visualization

Make it extremely visual and descriptive so an image generator can create it. Use phrases like "on the left side", "connected by blue arrows", "enclosed in a VPC boundary box", etc."""

    try:
        claude_response = bedrock_client.invoke_model(
            modelId='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1500,
                'messages': [{
                    'role': 'user',
                    'content': description_prompt
                }]
            })
        )
        
        claude_result = json.loads(claude_response['body'].read())
        visual_description = claude_result['content'][0]['text']
        
        print(f"\n📝 Architecture Description:\n{visual_description}\n")
        
        # Step 2: Use Titan to generate the diagram image
        titan_prompt = f"Professional AWS cloud architecture diagram: {visual_description[:500]}"
        
        titan_request = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": titan_prompt,
                "negativeText": "blurry, low quality, distorted, cartoon, amateur"
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "quality": "premium",
                "height": 1024,
                "width": 1024,
                "cfgScale": 8.0,
                "seed": int(time.time()) % 2147483647
            }
        }
        
        print("🎨 Generating diagram with Amazon Titan Image Generator...")
        
        titan_response = bedrock_client.invoke_model(
            modelId="amazon.titan-image-generator-v1",
            body=json.dumps(titan_request)
        )
        
        titan_response_body = json.loads(titan_response['body'].read())
        
        if titan_response_body.get('images'):
            image_b64 = titan_response_body['images'][0]
            image_bytes = base64.b64decode(image_b64)
            
            filename = DIAGRAM_OUTPUT_DIR / f"aws_diagram_{uuid4().hex[:8]}_{int(time.time())}.png"
            
            with open(filename, "wb") as f:
                f.write(image_bytes)
            
            print(f"✅ Diagram saved: {filename.absolute()}\n")
            return filename
        else:
            print("❌ No image generated in response")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Test the function
    request = "Create a simple S3 and CloudFront architecture for hosting a static website"
    diagram_path = generate_architecture_diagram(request)
    
    if diagram_path:
        print(f"📊 Open diagram: open {diagram_path}")
