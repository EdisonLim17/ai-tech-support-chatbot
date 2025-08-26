import json
import boto3
import time

ddb = boto3.resource('dynamodb', region_name='us-east-1')
tb = ddb.Table('chatbot-conversations')

def handler(event, context):
    route = event.get("requestContext", {}).get("routeKey")
    if route == "$connect":
        # Handle new connection
        return {"statusCode": 200, "body": "Connection established"}
    elif route == "$disconnect":
        # Handle disconnection
        return {"statusCode": 200, "body": "Connection terminated"}
    elif route == "sendMessage":
        # Handle incoming message
        userMessage = event.get("body", {})

        # Store new message in DynamoDB
        conversation_id = event.get("requestContext", {}).get("connectionId")
        tb.put_item(Item={
            'session_id': conversation_id,
            'timestamp': int(time.time()),
            'sender': 'user',
            'message': userMessage
        })

        #Fetch conversation history


        return {"statusCode": 200, "body": "Message received: " + userMessage}
    else:
        # Handle unknown route
        return {"statusCode": 400, "body": "Unknown route"}