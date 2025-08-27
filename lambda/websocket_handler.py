import json
import boto3
import time
import logging

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
            userMessage = json.loads(rawUserMessage).get("body")
        except Exception as e:
            return {"statusCode": 400, "body": "Invalid message format"}

        # Store new message in DynamoDB
        tb.put_item(Item={  
            'session_id': conversation_id,
            'timestamp': int(time.time()),
            'sender': 'user',
            'message': userMessage
        })

        #Fetch conversation history

        #Pass message to Bedrock model and get response
        try:
            system_prompt = "You are a helpful technical support assistant. Provide concise and accurate answers to user queries."
            messages = []
            messages.append({"role": "user", "content": [{"type": "text", "text": system_prompt}]})
            messages.append({"role": "user", "content": [{"type": "text", "text": userMessage}]})

            response = bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": messages,
                    "max_tokens": 64,
                    "temperature": 0.2
                    }),
                contentType='application/json',
                accept='application/json'
            )
        except Exception as e:
            logger.error("Error invoking Bedrock model: %s", str(e))
            mgmt_api.post_to_connection(
                ConnectionId=conversation_id,
                Data=json.dumps({"statusCode": 500, "body": "Error invoking Bedrock model: " + str(e)}).encode('utf-8')
            )
            return {"statusCode": 500, "body": "Error invoking Bedrock model: " + str(e)}

        #Process Bedrock response
        try:
            responseBody = json.loads(response['body'].read().decode('utf-8'))
            logger.info("Bedrock raw response: %s", responseBody)
            chatbotResponse = responseBody["content"][0]["text"]
            logger.info("Bedrock response: %s", chatbotResponse)
        except Exception as e:
            logger.error("Error processing Bedrock response: %s", str(e))
            mgmt_api.post_to_connection(
                ConnectionId=conversation_id,
                Data=json.dumps({"statusCode": 500, "body": "Error processing Bedrock response: " + str(e)}).encode('utf-8')
            )
            return {"statusCode": 500, "body": "Error processing Bedrock response: " + str(e)}

        # Store chatbot response in DynamoDB
        tb.put_item(Item={
            'session_id': conversation_id,
            'timestamp': int(time.time()),
            'sender': 'chatbot',
            'message': chatbotResponse
        })

        #Send response back to client
        mgmt_api.post_to_connection(
            ConnectionId=conversation_id,
            Data=json.dumps({"body": chatbotResponse}).encode('utf-8')
        )


        return {"statusCode": 200, "body": "Message received! Response: " + chatbotResponse}
    else:
        # Handle unknown route
        return {"statusCode": 400, "body": "Unknown route"}