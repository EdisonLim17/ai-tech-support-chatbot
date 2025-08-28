import json
import boto3
import time
import logging
from boto3.dynamodb.conditions import Key

import re

MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
SYSTEM_PROMPT = (
    "You are TechAssist, the virtual support assistant for a SaaS cloud platform.\n"
    "Your job is to help customers with technical support, account issues, and general product guidance.\n\n"
    "Tone & Style:\n"
    "- Be professional, concise, and friendly.\n"
    "- Use clear step-by-step instructions for troubleshooting.\n"
    "- Prefer bullet points or short paragraphs for readability.\n"
    "- Never use slang or informal jokes.\n"
    "- Always maintain a helpful, supportive attitude.\n\n"
    "Hard Rules (must follow):\n"
    "- Do not invent product features, policies, or information.\n"
    "- Never provide personal, financial, or legal advice.\n"
    "- Never guess about billing, refunds, or security policies — escalate instead.\n"
    "- Do not expose or ask for PII (names, account IDs, passwords, SSNs, payment details). If present, redact and escalate.\n"
    "- Only include links from allowed_domains: [\"example.com\", \"docs.example.com\"]. Strip other links.\n"
    "- If asked for pricing/contract/legal/medical advice, respond with escalation message.\n\n"
    "Escalation logic:\n"
    "- If the request is outside known topics, unclear, or confidence is low, set \"escalation\": true.\n"
    "- If you had to redact sensitive content, set \"escalation\": true.\n\n"
    "Output format (MUST be valid JSON only, no extra commentary):\n"
    "{\n"
    "  \"answer\": \"<customer-facing reply text>\",\n"
    "  \"steps\": [\"<optional step 1>\", \"<optional step 2>\"],\n"
    "  \"resources\": [\"<optional helpful link>\"],\n"
    "  \"confidence\": 0.0 to 1.0,\n"
    "  \"escalation\": true|false\n"
    "}\n\n"
    "Example:\n"
    "User: \"How do I reset my password?\"\n"
    "Assistant JSON Response:\n"
    "{\n"
    "  \"answer\": \"You can reset your password by using the 'Forgot Password' link on the login page.\",\n"
    "  \"steps\": [\"Go to the login page.\", \"Click 'Forgot Password'.\", \"Check your email for a reset link and follow the instructions.\"],\n"
    "  \"resources\": [\"https://example.com/help/reset-password\"],\n"
    "  \"confidence\": 0.95,\n"
    "  \"escalation\": false\n"
    "}\n"
)

ALLOWED_DOMAINS = ["example.com", "docs.example.com"]

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

        #Validate and enrich response
        try:
            validatedResponse = validate_and_enrich_response(chatbotResponse)

            # Build a plain-text response by joining lists safely
            answer = validatedResponse.get("answer", "") or ""
            steps = validatedResponse.get("steps", []) or []
            resources = validatedResponse.get("resources", []) or []

            steps_text = ""
            if steps:
                # prefix each step for readability
                steps_text = "\n\nSteps:\n" + "\n".join(f"- {s}" for s in steps if isinstance(s, str))

            resources_text = ""
            if resources:
                resources_text = "\n\nHere are some useful resources:\n" + "\n".join([r for r in resources if isinstance(r, str)])

            validatedResponseBody = answer + steps_text + resources_text
        except ValueError as ve:
            logger.error("Response validation error: %s", str(ve))
            validatedResponse = {
                "answer": "I'm sorry, but I am unable to process your request at this time. A human support agent will assist you shortly.",
                "steps": [],
                "resources": [],
                "confidence": 0.0,
                "escalation": True,
                "tags": ["INVALID_OUTPUT"]
            }
            validatedResponseBody = validatedResponse.get("answer", "")
        except Exception as e:
            logger.error("Unexpected error during response validation: %s", str(e))
            validatedResponse = {
                "answer": "I'm sorry, but I am unable to process your request at this time. A human support agent will assist you shortly.",
                "steps": [],
                "resources": [],
                "confidence": 0.0,
                "escalation": True,
                "tags": ["PROCESSING_ERROR"]
            }
            validatedResponseBody = validatedResponse.get("answer", "")

        #Send response back to client
        mgmt_api.post_to_connection(
            ConnectionId=conversation_id,
            Data=validatedResponseBody.encode('utf-8')
        )

        return {"statusCode": 200, "body": "Message received! Response: " + validatedResponseBody}
    
    else:
        # Handle unknown route
        return {"statusCode": 400, "body": "Unknown route"}


#Gets the user message from the event, stores it in DynamoDB, and returns the message text
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

#Fetches the last 10 messages from DynamoDB for the given conversation_id
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
    
#Calls the Bedrock model with the conversation messages and returns the raw response
def callBedrockModel(mgmt_api, conversation_id, messages):
    try:
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "system": SYSTEM_PROMPT,
                "messages": messages,
                "max_tokens": 1024,
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
    
#Processes the Bedrock response, stores it in DynamoDB, and returns the chatbot message text
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

# Post-validation: validates model output JSON, enforces rules, redacts sensitive content, and filters resource links.
def validate_and_enrich_response(response_text):
    """Validate the model response (JSON string or dict) against the expected schema and enforce business rules.

    This function now accepts either a JSON string or a dict. If the input is a string and
    json.loads fails, it will attempt to extract the first JSON object substring and parse that.
    """
    # Accept dicts directly (processBedrockResponse may already return parsed JSON)
    if isinstance(response_text, dict):
        parsed = response_text
    else:
        # Ensure we have a str
        raw = response_text if isinstance(response_text, str) else str(response_text)
        try:
            parsed = json.loads(raw)
        except Exception:
            # Attempt to extract a JSON object substring as a best-effort recovery
            try:
                start = raw.find('{')
                end = raw.rfind('}')
                if start != -1 and end != -1 and end > start:
                    candidate = raw[start:end+1]
                    parsed = json.loads(candidate)
                else:
                    logger.error("Failed to parse JSON from model response. raw len=%d preview=%s", len(raw), raw[:200])
                    raise ValueError("INVALID_OUTPUT: response is not valid JSON")
            except Exception:
                logger.error("Failed to recover JSON from model response. raw len=%d preview=%s", len(raw), raw[:200])
                raise ValueError("INVALID_OUTPUT: response is not valid JSON")

    # Basic schema and types
    answer = parsed.get("answer")
    steps = parsed.get("steps", [])
    resources = parsed.get("resources", [])
    confidence = parsed.get("confidence")
    escalation = bool(parsed.get("escalation", False))
    tags = parsed.get("tags", []) if isinstance(parsed.get("tags", []), list) else []

    if not isinstance(answer, str) or answer.strip() == "":
        raise ValueError("INVALID_OUTPUT: missing or empty 'answer'")

    if not isinstance(steps, list):
        steps = []
    if not isinstance(resources, list):
        resources = []

    # Normalize confidence
    try:
        confidence = float(confidence) if confidence is not None else 0.0
    except Exception:
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    # Check for disallowed sensitive phrases
    # Patterns matching: SSN/SIN, passport, credit card, ipv4, ipv6
    sensitive_patterns = [
        re.compile(r"\b(?:\d{3}-\d{2}-\d{4}|\d{3}-\d{3}-\d{3}|\d{9})\b"),  # SSN/SIN variants
        re.compile(r"\b[A-Z]{2}\d{6}\b", re.IGNORECASE),  # passport-like: 2 letters + 6 digits
        re.compile(r"\b(?:\d[ \-]?){13,19}\b"),  # credit-card like sequences 13-19 digits allowing spaces/dashes
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),  # IPv4
        re.compile(r"\b(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}\b", re.IGNORECASE),  # IPv6
    ]
    for p in sensitive_patterns:
        if p.search(answer):
            # redact and escalate
            return {
                "answer": "Response contained sensitive content and was redacted. Escalating to human support.",
                "steps": [],
                "resources": [],
                "confidence": 0.0,
                "escalation": True,
                "tags": tags + ["REDACTED"]
            }

    # Filter resources to allowed domains
    filtered_resources = []
    for url in resources:
        try:
            # simple check: domain substring
            if any(d in url for d in ALLOWED_DOMAINS):
                filtered_resources.append(url)
            else:
                tags.append("REMOVED_LINK")
        except Exception:
            # skip malformed URLs
            tags.append("INVALID_RESOURCE")

    validated = {
        "answer": answer.strip(),
        "steps": [s for s in steps if isinstance(s, str)],
        "resources": filtered_resources,
        "confidence": confidence,
        "escalation": bool(escalation),
        "tags": list(dict.fromkeys(tags))
    }

    # If confidence very low, force escalation
    if validated["confidence"] < 0.2:
        validated["escalation"] = True
        if "LOW_CONFIDENCE" not in validated["tags"]:
            validated["tags"].append("LOW_CONFIDENCE")

    return validated

