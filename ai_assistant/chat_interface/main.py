from uuid import uuid4
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

from agent.query_pipeline import QueryPipeline

app = FastAPI()
query_pipeline = QueryPipeline()

# Serve the static index.html
@app.get("/", response_class=HTMLResponse)
async def get():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(index_path, "r") as f:
        return HTMLResponse(f.read())

# Simple WebSocket endpoint for chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid4())
    
    try:    
        while True:
            user_input = await websocket.receive_text()
            print(f"Received text {user_input} with session id {session_id}")
            async for chunk in query_pipeline.run(user_query=user_input, session_id=session_id):
                await websocket.send_text(chunk)
    except WebSocketDisconnect:
        print(f"🔌 Client disconnected: {session_id}")
