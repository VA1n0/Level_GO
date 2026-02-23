from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random, math, time
from typing import Dict, List

app = FastAPI()

# ✅ CORS (поки відкрито, потім звузиш до Vercel домену)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Центр Ратного
RATNE_CENTER_LAT = 51.671708
RATNE_CENTER_LON = 24.524050

# ✅ Радіуси
SPAWN_RADIUS_M = 1200
PICKUP_RADIUS_M = 30

# --- In-memory state ---
drops: List[dict] = []
users: Dict[str, dict] = {}   # user_id -> {"inv": {...}, "last": ts}


# --- Helpers ---
def random_point_around(lat: float, lon: float, radius_m: float):
    # рівномірно по площі
    r = radius_m * math.sqrt(random.random())
    theta = random.random() * 2 * math.pi

    # метри -> градуси
    dlat = (r * math.cos(theta)) / 111_320.0
    dlon = (r * math.sin(theta)) / (111_320.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_user(uid: str) -> dict:
    if uid not in users:
        users[uid] = {
            "inv": {"зерно": 0, "круасан": 0, "золота чашка": 0},
            "last": time.time(),
        }
    return users[uid]


def compute_rewards(inv: dict) -> dict:
    # MVP:
    # 5 круасанів = -5%
    # 10 круасанів = -10%
    # 1 золота чашка = -15%
    cro = inv.get("круасан", 0)
    gold = inv.get("золота чашка", 0)

    discount = 0
    if cro >= 10:
        discount = max(discount, 10)
    elif cro >= 5:
        discount = max(discount, 5)

    if gold >= 1:
        discount = max(discount, 15)

    return {"discount_percent": discount}


# --- Models ---
class CollectRequest(BaseModel):
    user_id: str
    drop_id: int
    lat: float
    lon: float


# --- Routes ---
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/drops")
def get_drops():
    return {"drops": drops, "pickup_radius_m": PICKUP_RADIUS_M}


@app.get("/spawn")
def spawn():
    global drops
    drops = []
    for i in range(20):
        lat, lon = random_point_around(RATNE_CENTER_LAT, RATNE_CENTER_LON, SPAWN_RADIUS_M)
        drops.append({
            "id": i,
            "lat": lat,
            "lon": lon,
            "type": random.choice(["зерно", "круасан", "золота чашка"])
        })
    return {
        "spawned": True,
        "count": len(drops),
        "center": [RATNE_CENTER_LAT, RATNE_CENTER_LON],
        "radius_m": SPAWN_RADIUS_M
    }


@app.get("/me")
def me(user_id: str):
    u = get_user(user_id)
    return {"user_id": user_id, "inv": u["inv"], "rewards": compute_rewards(u["inv"])}


@app.post("/collect")
def collect(body: CollectRequest):
    global drops

    d = next((x for x in drops if x["id"] == body.drop_id), None)
    if not d:
        return {"ok": False, "reason": "not_found"}

    dist = haversine_m(body.lat, body.lon, d["lat"], d["lon"])

    if dist > PICKUP_RADIUS_M:
        return {
            "ok": False,
            "reason": "too_far",
            "distance_m": round(dist, 1),
            "pickup_radius_m": PICKUP_RADIUS_M
        }

    # ✅ remove drop
    drops = [x for x in drops if x["id"] != body.drop_id]

    # ✅ add to inventory
    u = get_user(body.user_id)
    t = d["type"]
    u["inv"][t] = u["inv"].get(t, 0) + 1
    u["last"] = time.time()

    return {
        "ok": True,
        "collected": {"id": d["id"], "type": t},
        "inv": u["inv"],
        "rewards": compute_rewards(u["inv"]),
        "distance_m": round(dist, 1),
    }