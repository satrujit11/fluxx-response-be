from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
import shutil
import os
import uuid
from typing import Optional

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_URI = "mongodb://mongo:mrxap2n2n03seood@216.48.182.81:23652"
client = AsyncIOMotorClient(MONGO_URI)
db = client["driver_db"]
collection = db["drivers"]

# Directory to store uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount uploads directory to serve files publicly
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# Function to save uploaded files with unique names
def save_file(file: UploadFile):
    file_ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path


# API Endpoint to register a driver
@app.post("/register")
async def register_driver(
    name: str = Form(...),
    address: str = Form(...),
    aadharNumber: str = Form(...),
    vehicle: str = Form(...),
    city: str = Form(...),
    panNumber: Optional[str] = Form(None),
    dlNumber: Optional[str] = Form(None),
    aadharFile: UploadFile = File(...),
    panFile: Optional[UploadFile] = File(None),
    dlFile: Optional[UploadFile] = File(None),
    riderPhoto: UploadFile = File(...),
):
    try:
        # Save required files
        aadhar_path = save_file(aadharFile)
        rider_photo_path = save_file(riderPhoto)

        # Save optional files if provided
        pan_path = save_file(panFile) if panFile else None
        dl_path = save_file(dlFile) if dlFile else None

        # Prepare driver data
        driver_data = {
            "name": name,
            "address": address,
            "city": city,
            "aadharNumber": aadharNumber,
            "vehicle": vehicle,
            "aadharFile": aadhar_path,
            "riderPhoto": rider_photo_path,
        }

        # Add optional fields if present
        if panNumber:
            driver_data["panNumber"] = panNumber
        if dlNumber:
            driver_data["dlNumber"] = dlNumber
        if pan_path:
            driver_data["panFile"] = pan_path
        if dl_path:
            driver_data["dlFile"] = dl_path

        # Save to MongoDB
        result = await collection.insert_one(driver_data)
        return {"message": "Driver registered successfully", "id": str(result.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoint to get all drivers
@app.get("/drivers")
async def get_drivers():
    try:
        drivers = await collection.find().to_list(100)
        
        # Convert ObjectId to string for each document
        for driver in drivers:
            driver["_id"] = str(driver["_id"])
        
        return drivers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/")
async def root():
    return {"message": "FastAPI File Upload with MongoDB"}

