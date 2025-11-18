import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import LeadJob, Lead, User

app = FastAPI(title="Denflow AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LeadRequest(BaseModel):
    location: str = Field(..., min_length=2)
    job_title: str = Field(..., min_length=2)
    company_size_range: str = Field(..., min_length=1)
    industry_keywords: List[str] = Field(..., min_items=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "Denflow AI API is running"}


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


# ---- Auth (demo) ----
@app.post("/auth/login")
def login(payload: LoginRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    # Simple demo auth: find or create user, no real password hashing
    user = db["user"].find_one({"email": payload.email})
    if not user:
        user_id = create_document("user", User(email=payload.email, password_hash="demo", auth_provider="password"))
        user = db["user"].find_one({"_id": ObjectId(user_id)})
    token = str(user["_id"])  # demo token
    return {"token": token, "user": {"email": user.get("email"), "name": user.get("name")}}


@app.post("/auth/google")
def google_auth(payload: GoogleAuthRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    user = db["user"].find_one({"email": payload.email})
    if not user:
        user_id = create_document("user", User(email=payload.email, name=payload.name or "", auth_provider="google"))
        user = db["user"].find_one({"_id": ObjectId(user_id)})
    token = str(user["_id"])  # demo token
    return {"token": token, "user": {"email": user.get("email"), "name": user.get("name")}}


@app.get("/auth/me")
def me(token: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        user = db["user"].find_one({"_id": ObjectId(token)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"email": user.get("email"), "name": user.get("name")}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")


# ---- Lead generation (demo) ----
@app.post("/api/leads/request")
def request_leads(payload: LeadRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    job = LeadJob(
        location=payload.location,
        job_title=payload.job_title,
        company_size_range=payload.company_size_range,
        industry_keywords=payload.industry_keywords,
        status="processing",
        result_count=0,
    )
    job_id = create_document("leadjob", job)

    # Demo: generate mock leads immediately and mark job as ready
    mock_leads = []
    for i in range(1, 11):
        lead = Lead(
            job_id=job_id,
            name=f"Contact {i}",
            email=f"contact{i}@example.com",
            phone=f"+1-202-555-01{i:02d}",
            linkedin=f"https://linkedin.com/in/contact{i}",
            company=f"Company {i}",
            title=payload.job_title,
            location=payload.location,
            company_size=payload.company_size_range,
            industry=payload.industry_keywords[0]
        )
        create_document("lead", lead)
        mock_leads.append(lead)

    db["leadjob"].update_one({"_id": ObjectId(job_id)}, {"$set": {"status": "ready", "result_count": len(mock_leads)}})

    return {"job_id": job_id, "status": "processing", "message": "Your leads are being generated. You'll be notified when ready."}


@app.get("/api/leads/status/{job_id}")
def get_lead_status(job_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        job = db["leadjob"].find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {
            "status": job.get("status", "processing"),
            "result_count": job.get("result_count", 0)
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job id")


@app.get("/api/leads/results/{job_id}")
def get_lead_results(job_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        _ = ObjectId(job_id)
        leads = get_documents("lead", {"job_id": job_id}, limit=200)
        for l in leads:
            l["_id"] = str(l["_id"])
        return {"leads": leads}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job id")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
