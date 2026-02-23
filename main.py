from fastapi import FastAPI
import random

app = FastAPI()

drops = []

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/drops")
def get_drops():
    return drops

@app.post("/spawn")
def spawn():
    global drops
    drops = [
        {
            "id": i,
            "lat": 51.345 + random.uniform(-0.01, 0.01),
            "lon": 24.55 + random.uniform(-0.01, 0.01),
            "type": random.choice(["зерно", "круасан", "золота чашка"])
        }
        for i in range(10)
    ]
    return {"spawned": True}