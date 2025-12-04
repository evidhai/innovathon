import os
import json
import time
import boto3
import pprint
import logging

from botocore.exceptions import ClientError

# -------------------------------
# AWS CONFIGURATION
# -------------------------------
aws_region = "us-east-1"
session = boto3.Session(region_name=aws_region)

s3 = session.client("s3")
iam = session.client("iam")
aoss_client = session.client("opensearchserverless")
bedrock_agent = session.client("bedrock-agent")



def interactive_sleep(seconds: int) -> None:
    """
    Sleep with prints to the user
    """
    dots = ""
    for _ in range(seconds):
        dots += "."
        print(dots, end="\r")
        time.sleep(1)


# -------------------------------
# RESOURCE NAMES
# -------------------------------
bucket_name = "bedrock-kb-innovation"
aoss_collection_name = "bedrock-kb-collection"
aoss_index_name = "bedrock-kb-index"
bedrock_kb_name = "bedrock-kb-for-agent"


embedding_model_id = "amazon.titan-embed-text-v2:0"
embedding_model_arn = f"arn:aws:bedrock:{aws_region}::foundation-model/{embedding_model_id}"

local_data_dir = "kb_documents"


# ---------------------------------------------------
# HELPER: Create Execution Role
# ---------------------------------------------------
def create_bedrock_execution_role(bucket_name):
    role_name = "BedrockKBExecutionRole"

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    try:
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        print("Created IAM Role:", role_name)

    except iam.exceptions.EntityAlreadyExistsException:
        role = iam.get_role(RoleName=role_name)
        print("IAM Role already exists:", role_name)

    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": ["aoss:*"],
                "Resource": "*"
            }
        ]
    }

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="BedrockKBS3AOSSPolicy",
        PolicyDocument=json.dumps(policy_doc)
    )

    return role

# ---------------------------------------------------
# HELPER: Create AOSS Policies
# ---------------------------------------------------
def create_policies_in_oss(aoss_collection_name: str, aoss_client: boto3.client, bedrock_kb_execution_role_arn: str) -> tuple[dict, dict, dict]:
    encryption_policy_name = f"bedrock-sample-rag-sp" 
    network_policy_name = f"bedrock-sample-rag-np" 
    access_policy_name = f"bedrock-sample-rag-ap" 

    encryption_policy = aoss_client.create_security_policy( 
        name=encryption_policy_name, 
        policy=json.dumps( { 
            "Rules": [ 
                { 
                    "Resource": ["collection/" + aoss_collection_name], 
                    "ResourceType": "collection", 
                } 
            ], 
            "AWSOwnedKey": True, 
        } ), 
        type="encryption", 
    ) 

    network_policy = aoss_client.create_security_policy(
        name=network_policy_name,
        policy=json.dumps([
            {
                "Rules": [
                    {
                        "Resource": ["collection/" + aoss_collection_name],
                        "ResourceType": "collection",
                    }
                ],
                "AllowFromPublic": True,
            }
        ]),
        type="network",
    )

    access_policy = aoss_client.create_access_policy(
        name=access_policy_name,
        policy=json.dumps([
            {
                "Rules": [
                    {
                        "Resource": ["collection/" + aoss_collection_name],
                        "Permission": [
                            "aoss:CreateCollectionItems",
                            "aoss:DeleteCollectionItems",
                            "aoss:UpdateCollectionItems",
                            "aoss:DescribeCollectionItems",
                        ],
                        "ResourceType": "collection",
                    },
                    {
                        "Resource": ["index/" + aoss_collection_name + "/*"],
                        "Permission": [
                            "aoss:CreateIndex",
                            "aoss:DeleteIndex",
                            "aoss:UpdateIndex",
                            "aoss:DescribeIndex",
                            "aoss:ReadDocument",
                            "aoss:WriteDocument",
                        ],
                        "ResourceType": "index",
                    },
                ],
                "Principal": [bedrock_kb_execution_role_arn],
                "Description": "Easy data policy",
            }
        ]),
        type="data",
    )

    return encryption_policy, network_policy, access_policy

def create_os_polices_and_collection(aoss_client: boto3.client) -> tuple[dict, str, str]:
    """
    Create security, network, and data access policies within OpenSearch Serverless (OSS),
    and create an OSS collection for the vector store.

    Args:
        aoss_client (boto3.client): The boto3 client for OpenSearch Serverless.

    Returns:
        tuple[dict, str, str]: A tuple containing the created collection, collection ID, and Bedrock execution role ARN.
    """
    bedrock_kb_execution_role = create_bedrock_execution_role(
        bucket_name=bucket_name
    )
    bedrock_kb_execution_role_arn = bedrock_kb_execution_role["Role"]["Arn"]
    encryption_policy, network_policy, access_policy = (
        create_policies_in_oss(
            aoss_collection_name = aoss_collection_name,
            aoss_client= aoss_client,
            bedrock_kb_execution_role_arn=bedrock_kb_execution_role_arn,
        )
    )
    # kb_info.access_policy_name = access_policy["accessPolicyDetail"]["name"]
    # kb_info.network_policy_name = network_policy["securityPolicyDetail"][
    #     "name"
    # ]
    # kb_info.encryption_policy_name = encryption_policy["securityPolicyDetail"][
    #     "name"
    # ]

    aoss_collection = aoss_client.create_collection(
        name=aoss_collection_name, type="VECTORSEARCH"
    )
    pprint.PrettyPrinter(indent=2).pprint(aoss_collection)

    collection_id = aoss_collection["createCollectionDetail"]["id"]
    # kb_info.collection_id = collection_id

    # create opensearch serverless access policy and attach it to Bedrock execution role
    # kb_roles.create_oss_policy_attach_bedrock_execution_role(
    #     collection_id=collection_id,
    #     bedrock_kb_execution_role=bedrock_kb_execution_role,
    # )

    return aoss_collection, collection_id, bedrock_kb_execution_role_arn


# ---------------------------------------------------
# STEP 1: Create bucket
# ---------------------------------------------------
try:
    s3.head_bucket(Bucket=bucket_name)
    print(f"S3 bucket '{bucket_name}' already exists.")
except ClientError:
    print(f"Creating S3 bucket '{bucket_name}'...")
    s3.create_bucket(Bucket=bucket_name)
    print("Bucket created successfully.")

# ---------------------------------------------------
# STEP 2: Upload PDFs
# ---------------------------------------------------
for root, _, files in os.walk(local_data_dir):
    for file in files:
        if file.lower().endswith(".pdf"):
            s3.upload_file(os.path.join(root, file), bucket_name, file)
            print("Uploaded:", file)

# ---------------------------------------------------
# STEP 3: Create IAM role
# ---------------------------------------------------
role = create_bedrock_execution_role(bucket_name)
role_arn = role["Role"]["Arn"]
print("Execution Role ARN:", role_arn)

# # ---------------------------------------------------
# # STEP 4: Create AOSS Policies
# # ---------------------------------------------------
# print("Creating AOSS security policies...")
# aoss_collection, collection_id, bedrock_role_arn     = create_os_polices_and_collection(aoss_client=aoss_client)
# print("AOSS security policies created.")

# # ---------------------------------------------------
# # STEP 5: Create AOSS Collection
# # ---------------------------------------------------

# # wait for collection creation
# # This can take couple of minutes to finish
# # Periodically check collection status
# response = aoss_client.batch_get_collection(names=[aoss_collection_name])

# while (response["collectionDetails"][0]["status"]) == "CREATING":
#     print("Creating collection...")
#     interactive_sleep(30)
#     response = aoss_client.batch_get_collection(names=[aoss_collection_name])

# print("\nCollection successfully created:")
# pprint.PrettyPrinter(indent=2).pprint(response["collectionDetails"])

# # It can take up to a minute for data access rules to be enforced
# interactive_sleep(60)

# ---------------------------------------------------
# STEP 6: Create AOSS Index
# ---------------------------------------------------

# VECTOR_DIMENSION = 1536  # Titan v2 embedding dimensionality
# collection_response = aoss_client.batch_get_collection(names=[aoss_collection_name])
# response = aoss_client.create_index(
#     id        = collection_response["collectionDetails"][0]["id"],
#     indexName= aoss_index_name,
#     indexSchema= {
#     "settings": {
#         "index": {
#             "knn": True,
#             "knn.space_type": "cosinesimil",
#         }
#     },
#     "mappings": {
#         "properties": {
#             "embedding": { 
#                 "type": "knn_vector",
#                 "dimension": VECTOR_DIMENSION
#             },
#             "text": {"type": "text"},
#             "metadata": {"type": "object"},
#         }
#     }
# }
# )
# VECTOR_DIMENSION = 1536
# VECTOR_DIMENSION = 1536

# def create_aoss_index(aoss_client, collection_name, index_name):
#     # First, get the collection details
#     collection = aoss_client.batch_get_collection(names=[collection_name])
#     collection_id = collection["collectionDetails"][0]["id"]

#     # Then, create the index
#     response = aoss_client.create_index(
#         name=index_name,
#         type="VECTOR",
#         collectionId=collection_id,  # <-- use collectionId, not indices namespace
#         indexSchema={
#             "settings": {
#                 "index": {
#                     "knn": True,
#                     "knn.space_type": "cosinesimil"
#                 }
#             },
#             "mappings": {
#                 "properties": {
#                     "embedding": {"type": "knn_vector", "dimension": VECTOR_DIMENSION},
#                     "text": {"type": "text"},
#                     "metadata": {"type": "object"},
#                 }
#             }
#         }
#     )
#     return response

# create_aoss_index(aoss_client, aoss_collection_name, aoss_index_name)


# ---------------------------------------------------
# STEP 6: Create Knowledge Base
# ---------------------------------------------------
print("Creating Bedrock Knowledge Base...")


kb = bedrock_agent.create_knowledge_base(
    name=bedrock_kb_name,
    roleArn=role_arn,
    knowledgeBaseConfiguration={
        "type": "VECTOR",
        "vectorKnowledgeBaseConfiguration": {
            "embeddingModelArn": embedding_model_arn
        }
    },
    storageConfiguration={
        "type": "OPENSEARCH_SERVERLESS",
        "opensearchServerlessConfiguration": {
            "collectionArn": "arn:aws:aoss:us-east-1:095059577505:collection/nkctdyjpcljgz9zj85e0",
            "vectorIndexName": aoss_index_name,
            "fieldMapping": {
                "vectorField": "embedding",
                "textField": "text",
                "metadataField": "metadata"
            }
        }
    }
)

print("Knowledge Base Created:")
print(json.dumps(kb, indent=2))

print("\n🎉 Setup completed successfully!")
