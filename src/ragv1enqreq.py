import json
from ragv1 import answer_query

# Simulate frontend passing a query

def lambda_handler(event):
    body = json.loads(event["body"])
    user_query = body.get("query")
    session_id = body.get("session_id")

    if not user_query or not session_id:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing query or session_id"})}

    try:
        answer, image = answer_query(user_query, session_id)
        result = {"answer": answer}
        if image:
            import base64
            result["image_b64"] = base64.b64encode(image).decode("utf-8")
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}