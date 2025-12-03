import os
import sys
import json
import time
import random

# Third-party imports
import boto3
from botocore.exceptions import ClientError

# Local imports
import utility


# Create boto3 session and set AWS region
aws_region = "us-east-1"  # <--- your region
boto_session = boto3.Session(region_name=aws_region)

# Create boto3 clients for AOSS, Bedrock, and S3 services
aoss_client = boto3.client('opensearchserverless', region_name=aws_region)
bedrock_agent_client = boto3.client('bedrock-agent', region_name=aws_region)
s3_client = boto3.client('s3', region_name=aws_region)


# Define names for AOSS, Bedrock, and S3 resources
s3_bucket_name = f"bedrock-kb"
aoss_collection_name = f"bedrock-kb-collection"
aoss_index_name = f"bedrock-kb-index"
bedrock_kb_name = f"bedrock-kb-for-agent"

# Set the Bedrock model to use for embedding generation
embedding_model_id = 'amazon.titan-embed-text-v2:0'
embedding_model_arn = f'arn:aws:bedrock:{aws_region}::foundation-model/{embedding_model_id}'
embedding_model_dim = 1024

# Some temporary local paths
local_data_dir = 'data'

# Print configurations
print("AWS Region:", aws_region)
print("S3 Bucket:", s3_bucket_name)
print("AOSS Collects3_cliention Name:", aoss_collection_name)
print("Bedrock Knowledge Base Name:", bedrock_kb_name)


# Check if bucket exists, and if not create S3 bucket for KB data source

try:
    s3_client.head_bucket(Bucket=s3_bucket_name)
    print(f"Bucket '{s3_bucket_name}' already exists..")
except ClientError as e:
    print(f"Creating bucket: '{s3_bucket_name}'..")
    if aws_region == 'us-east-1':
        s3_client.create_bucket(Bucket=s3_bucket_name)
    else:
        s3_client.create_bucket(
            Bucket=s3_bucket_name,
            CreateBucketConfiguration={'LocationConstraint': aws_region}
        )

# Local folder containing your PDFs
local_data_dir = 'kb_documents'

# Upload all PDFs from local folder to S3
if not os.path.exists(local_data_dir):
    raise FileNotFoundError(f"Folder '{local_data_dir}' does not exist.")

for root, _, files in os.walk(local_data_dir):
    for file in files:
        if file.lower().endswith('.pdf'):
            full_path = os.path.join(root, file)
            s3_client.upload_file(full_path, s3_bucket_name, file)
            print(f"Uploaded: '{file}' to 's3://{s3_bucket_name}'")


# Create Bedrock execution role
bedrock_kb_execution_role = utility.create_bedrock_execution_role(bucket_name=s3_bucket_name)
bedrock_kb_execution_role_arn = bedrock_kb_execution_role['Role']['Arn']
print("Created KB execution role with ARN:", bedrock_kb_execution_role_arn)

# Create AOSS policies and attach to execution role
aoss_encryption_policy, aoss_network_policy, aoss_access_policy = utility.create_policies_in_oss(
    vector_store_name=aoss_collection_name,
    aoss_client=aoss_client,
    bedrock_kb_execution_role_arn=bedrock_kb_execution_role_arn
)

print("Created AOSS policies:")
print("Encryption policy:", aoss_encryption_policy['securityPolicyDetail']['name'])
print("Network policy:", aoss_network_policy['securityPolicyDetail']['name'])
print("Access policy:", aoss_access_policy['accessPolicyDetail']['name'])

# Create AOSS collection
aoss_collection = aoss_client.create_collection(name=aoss_collection_name, type='VECTORSEARCH')
print("Waiting until AOSS collection becomes active...", end='')
while True:
    response = aoss_client.list_collections(collectionFilters={'name': aoss_collection_name})
    status = response['collectionSummaries'][0]['status']
    if status in ('ACTIVE', 'FAILED'):
        print(" done.")
        break
    print('█', end='', flush=True)
    time.sleep(5)
print("AOSS collection created:", json.dumps(response['collectionSummaries'], indent=2))

# Attach policy to collection
aoss_policy_arn = utility.create_oss_policy_attach_bedrock_execution_role(
    collection_id=aoss_collection['createCollectionDetail']['id'],
    bedrock_kb_execution_role=bedrock_kb_execution_role
)


print("Waiting 60 seconds for policies to propagate...", end='')

for _ in range(12):     # 12 * 5 sec = 60 sec
    print('█', end='', flush=True)
    time.sleep(5)

print(" done.")
print("Attached policy ARN:", aoss_policy_arn)