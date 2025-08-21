import streamlit as st
import json
import requests

st.title("Local RAG Assistant")
session_id = st.text_input("Session ID", value="test-session")
query = st.text_area("Ask a question about your documents")

if st.button("Submit"):
    with st.spinner("Getting answer..."):
        event = {
            "body": json.dumps({"query": query, "session_id": session_id})
        }
        from ragv1enqreq import lambda_handler
        response = lambda_handler(event)
        body = json.loads(response["body"])

        if "answer" in body:
            st.success(body["answer"])
        else:
            st.error(body.get("error", "Unknown error"))

        if "image_b64" in body:
            import base64
            from io import BytesIO
            from PIL import Image
            img_bytes = base64.b64decode(body["image_b64"])
            image = Image.open(BytesIO(img_bytes))
            st.image(image, caption="Generated Chart")