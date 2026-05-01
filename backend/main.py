from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional
from world import World
from agent import WumpusAgent
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.get("/")
def read_root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/app/")


class InitRequest(BaseModel):
    width: int
    height: int
    num_pits: Optional[int] = None

class InferRequest(BaseModel):
    x: int
    y: int

global_world = None
global_agent = None

def get_full_state() -> Dict[str, Any]:
    if not global_world or not global_agent:
        return {}
    return {
        "world": global_world.get_state(),
        "agent": global_agent.get_agent_state()
    }

@app.post("/init")
def init_game(req: InitRequest):
    global global_world, global_agent
    global_world = World(req.width, req.height, req.num_pits)
    global_agent = WumpusAgent(global_world)
    # process first percepts on spawn
    global_agent.process_percepts()
    return {"message": "Game initialized", "state": get_full_state()}

@app.get("/state")
def get_state():
    if not global_agent:
        raise HTTPException(status_code=400, detail="Game not initialized")
    return get_full_state()

@app.post("/move")
def move_agent():
    if not global_agent:
        raise HTTPException(status_code=400, detail="Game not initialized")
    global_agent.move()
    return get_full_state()

@app.get("/percepts")
def get_percepts():
    if not global_agent:
        raise HTTPException(status_code=400, detail="Game not initialized")
    return global_world.get_percepts(global_agent.pos)

@app.post("/infer")
def infer_safety(req: InferRequest):
    if not global_agent:
        raise HTTPException(status_code=400, detail="Game not initialized")
    is_safe, steps_s = global_agent.kb.ask_is_safe((req.x, req.y))
    is_unsafe, steps_u = global_agent.kb.ask_is_unsafe((req.x, req.y))
    
    status = "UNKNOWN"
    if is_safe:
        status = "SAFE"
    elif is_unsafe:
        status = "UNSAFE"
        
    return {
        "status": status,
        "inference_steps": steps_s + steps_u
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
