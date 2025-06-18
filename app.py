import json
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import base64
import requests

# FastAPI app setup
app = FastAPI()

# Pydantic model for request body
class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

# Configuration
DATA_FILE = "tds_data.json"
AIPROXY_TOKEN = os.environ.get('AIPROXY_TOKEN')

# Custom Grok client for AI Proxy
class Grok:
    def __init__(self, api_key, model, base_url):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    async def chat_async(self, messages, max_tokens):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens
        }
        response = requests.post(f"{self.base_url}/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

# Initialize Grok
grok = Grok(api_key=AIPROXY_TOKEN, model="gpt-4o-mini", base_url="https://aiproxy.sanand.workers.dev/openai")

# Load data at startup
tds_data = {'discourse': [], 'github': []}
try:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            tds_data = json.load(f)
    else:
        print(f"{DATA_FILE} not found. Please run scrape_data.py to generate it.")
except Exception as e:
    print(f"Error loading data: {e}")

# API endpoint
@app.post("/api/")
async def answer_question(request: QuestionRequest):
    try:
        # Start timer to ensure response within 30 seconds
        start_time = datetime.now()
        
        # Process image if provided
        image_content = None
        if request.image:
            try:
                image_content = base64.b64decode(request.image)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid base64 image: {str(e)}")

        # Prepare context from scraped data
        context = []
        for post in tds_data['discourse']:
            context.append(f"Discourse Post (Topic: {post['title']}, URL: {post['url']}): {post['content']}")
        for file in tds_data['github']:
            context.append(f"GitHub File ({file['path']}): {file['content']}")

        # Truncate context to avoid token limits (approx. 5000 characters)
        context_str = ' '.join(context)[:5000]

        # Prepare prompt for Grok
        prompt = f"""
        You are a virtual Teaching Assistant for the Tools in Data Science course at IIT Madras (Jan 2025).
        Answer the following student question based on the course content and Discourse posts from Jan 1, 2025 to Apr 14, 2025.
        If an image is provided, assume it contains relevant context (e.g., a screenshot of a question) but do not process it directly.
        Provide a concise answer and include up to two relevant Discourse links in the format {{'url': 'link', 'text': 'description'}}.
        Format the response as a JSON object with 'answer' and 'links' fields.

        Question: {request.question}
        Context: {context_str}
        """
        
        # Query Grok via AI Proxy
        response = await grok.chat_async(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        # Parse response
        try:
            answer_data = json.loads(response['choices'][0]['message']['content'])
        except:
            answer_data = {
                "answer": response['choices'][0]['message']['content'],
                "links": []
            }
        
        # Ensure response is within 30 seconds
        elapsed_time = (datetime.now() - start_time).total_seconds()
        if elapsed_time > 30:
            raise HTTPException(status_code=504, detail="Response generation exceeded 30 seconds")
        
        return {
            "answer": answer_data.get("answer", "No relevant information found."),
            "links": answer_data.get("links", [])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")