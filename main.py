from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # потім звузимо до твого домену Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

drops = []

# ✅ Центр Ратного (як ти дав)
RATNE_CENTER_LAT = 51.671708
RATNE_CENTER_LON = 24.524050

def random_point_around(lat: float, lon: float, radius_m: float):
    """
    Випадкова точка в колі радіусом radius_m навколо (lat, lon).
    Результат: (lat2, lon2)
    """
    # рівномірно по площі
    r = radius_m * math.sqrt(random.random())
    theta = random.random() * 2 * math.pi

    # метри -> градуси
    dlat = (r * math.cos(theta)) / 111_320.0
    dlon = (r * math.sin(theta)) / (111_320.0 * math.cos(math.radians(lat)))

    return lat + dlat, lon + dlon

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/drops")
def get_drops():
    return drops

@app.get("/spawn")
def spawn():
    global drops

    # 🔥 тут керуєш розкидом:
    # 600 м = дуже близько
    # 1200 м = норм для смт
    radius_m = 1200

    drops = []
    for i in range(20):  # хочеш 10/20/50 — міняй
        lat, lon = random_point_around(RATNE_CENTER_LAT, RATNE_CENTER_LON, radius_m)
        drops.append({
            "id": i,
            "lat": lat,
            "lon": lon,
            "type": random.choice(["зерно", "круасан", "золота чашка"])
        })

    return {"spawned": True, "count": len(drops), "center": [RATNE_CENTER_LAT, RATNE_CENTER_LON], "radius_m": radius_m}