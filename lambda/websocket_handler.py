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
        body = event.get("body", {})
        # Process the message
        print(f"Received message: {body}")
        return {"statusCode": 200, "body": "Message received: " + body}
    else:
        # Handle unknown route
        return {"statusCode": 400, "body": "Unknown route"}