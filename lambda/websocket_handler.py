import json
import boto3
import time
import logging
from boto3.dynamodb.conditions import Key

MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
SYSTEM_PROMPT = "You are a helpful technical support assistant. Provide concise and accurate answers to user queries."

ddb = boto3.resource('dynamodb', region_name='us-east-1')
tb = ddb.Table('chatbot-conversations')

bedrock = boto3.client(service_name='bedrock', region_name='us-east-1')
bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    route = event.get("requestContext", {}).get("routeKey")
    conversation_id = event.get("requestContext", {}).get("connectionId")
    mgmt_api = boto3.client('apigatewaymanagementapi', endpoint_url=f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}")

    if route == "$connect":
        # Handle new connection
        return {"statusCode": 200, "body": "Connection established"}
    elif route == "$disconnect":
        # Handle disconnection
        return {"statusCode": 200, "body": "Connection terminated"}
    
    elif route == "sendMessage":
        # Handle incoming message
        rawUserMessage = event.get("body", {})
        try:
            userMessage = processUserMessage(mgmt_api, conversation_id, rawUserMessage)
        except Exception as e:
            return {"statusCode": 400, "body": "Invalid message format"}

        #Fetch conversation history (last 10 messages)
        try:
            conversation_history = fetchConversationHistory(mgmt_api, conversation_id)
        except Exception as e:
            return {"statusCode": 500, "body": "Error fetching conversation history: " + str(e)}

        #Prepare messages for Bedrock
        messages = []
        # Add most recent 10 messages for context
        for msg in reversed(conversation_history):
            role = "user" if msg['sender'] == 'user' else "assistant"
            messages.append({"role": role, "content": [{"type": "text", "text": msg['message']}]})
        logger.info("Messages sent to Bedrock: %s", messages)

        #Pass message to Bedrock model and get response
        try:
            rawBedrockResponse = callBedrockModel(mgmt_api, conversation_id, messages)
        except Exception as e:
            return {"statusCode": 500, "body": "Error invoking Bedrock model: " + str(e)}

        #Process chatbot response
        try:
            chatbotResponse = processBedrockResponse(mgmt_api, conversation_id, rawBedrockResponse)
        except Exception as e:
            return {"statusCode": 500, "body": "Error processing Bedrock response: " + str(e)}

        #Send response back to client
        mgmt_api.post_to_connection(
            ConnectionId=conversation_id,
            Data=json.dumps({"body": chatbotResponse}).encode('utf-8')
        )

        return {"statusCode": 200, "body": "Message received! Response: " + chatbotResponse}
    
    else:
        # Handle unknown route
        return {"statusCode": 400, "body": "Unknown route"}



def processUserMessage(mgmt_api, conversation_id, rawUserMessage):
    try:
        userMessage = json.loads(rawUserMessage).get("body")
    except Exception as e:
        logger.error("Error processing user message: %s", str(e))
        raise ValueError("Invalid message format: " + str(e))

    # Store new user message in DynamoDB
    tb.put_item(Item={  
        'session_id': conversation_id,
        'timestamp': int(time.time()),
        'sender': 'user',
        'message': userMessage
    })

    return userMessage


def fetchConversationHistory(mgmt_api, conversation_id):
    try:
        response = tb.query(
            KeyConditionExpression=Key('session_id').eq(conversation_id),
            ScanIndexForward=False,
            Limit=10
        )
        conversation_history = response.get('Items', [])
        logger.info("Conversation history: %s", conversation_history)
        return conversation_history
    except Exception as e:
        logger.error("Error fetching conversation history: %s", str(e))
        mgmt_api.post_to_connection(
            ConnectionId=conversation_id,
            Data=json.dumps({"statusCode": 500, "body": "Error fetching conversation history: " + str(e)}).encode('utf-8')
        )
        raise RuntimeError("Error fetching conversation history: " + str(e))
    

def callBedrockModel(mgmt_api, conversation_id, messages):
    try:
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "system": SYSTEM_PROMPT,
                "messages": messages,
                "max_tokens": 64,
                "temperature": 0.2
                }),
            contentType='application/json',
            accept='application/json'
        )
        logger.info("Bedrock raw response: %s", response)
        return response
    except Exception as e:
        logger.error("Error invoking Bedrock model: %s", str(e))
        mgmt_api.post_to_connection(
            ConnectionId=conversation_id,
            Data=json.dumps({"statusCode": 500, "body": "Error invoking Bedrock model: " + str(e)}).encode('utf-8')
        )
        raise RuntimeError("Error invoking Bedrock model: " + str(e))
    

def processBedrockResponse(mgmt_api, conversation_id, response):
    try:
        responseBody = json.loads(response['body'].read().decode('utf-8'))
        logger.info("Bedrock raw response body: %s", responseBody)
        chatbotResponse = responseBody["content"][0]["text"]
        logger.info("Bedrock processed response: %s", chatbotResponse)

        # Store chatbot response in DynamoDB
        tb.put_item(Item={
            'session_id': conversation_id,
            'timestamp': int(time.time()),
            'sender': 'chatbot',
            'message': chatbotResponse
        })

        return chatbotResponse
    except Exception as e:
        logger.error("Error processing Bedrock response: %s", str(e))
        mgmt_api.post_to_connection(
            ConnectionId=conversation_id,
            Data=json.dumps({"statusCode": 500, "body": "Error processing Bedrock response: " + str(e)}).encode('utf-8')
        )
        raise ValueError("Error processing Bedrock response: " + str(e))
    
