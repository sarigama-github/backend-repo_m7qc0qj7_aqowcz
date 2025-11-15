import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Restaurant, MenuItem, Order

app = FastAPI(title="Food Delivery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Food Delivery Backend Ready"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# ---------- Restaurants ----------
@app.post("/api/restaurants")
def create_restaurant(data: Restaurant):
    try:
        inserted_id = create_document("restaurant", data)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/restaurants")
def list_restaurants():
    try:
        docs = get_documents("restaurant")
        for d in docs:
            d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Menu Items ----------
@app.post("/api/menu")
def create_menu_item(data: MenuItem):
    try:
        # ensure restaurant exists
        rid = data.restaurant_id
        if not ObjectId.is_valid(rid):
            raise HTTPException(status_code=400, detail="Invalid restaurant_id")
        if db["restaurant"].count_documents({"_id": ObjectId(rid)}) == 0:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        inserted_id = create_document("menuitem", data)
        return {"id": inserted_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/menu/{restaurant_id}")
def get_menu_for_restaurant(restaurant_id: str):
    try:
        if not ObjectId.is_valid(restaurant_id):
            raise HTTPException(status_code=400, detail="Invalid restaurant_id")
        items = get_documents("menuitem", {"restaurant_id": restaurant_id})
        for i in items:
            i["id"] = str(i.pop("_id"))
        return items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Orders ----------
@app.post("/api/orders")
def place_order(order: Order):
    try:
        inserted_id = create_document("order", order)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
def list_orders():
    try:
        docs = get_documents("order")
        for d in docs:
            d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
