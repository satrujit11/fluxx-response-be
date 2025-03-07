from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import shutil
import os
import uuid
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# Enable CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this if frontend runs elsewhere
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# MongoDB Connection
MONGO_URI = "mongodb://mongo:mrxap2n2n03seood@216.48.182.81:23652"
client = AsyncIOMotorClient(MONGO_URI)
db = client["driver_db"]
collection = db["drivers"]

# Directory to store uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Pydantic Model for Data Validation
class DriverBase(BaseModel):
    name: str
    address: str
    aadharNumber: str
    panNumber: str
    dlNumber: str
    vehicle: str


# Function to save uploaded files with unique names
def save_file(file: UploadFile):
    file_ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"  # Generate a unique filename
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
    panNumber: str = Form(...),
    dlNumber: str = Form(...),
    vehicle: str = Form(...),
    aadharFile: UploadFile = File(...),
    panFile: UploadFile = File(...),
    dlFile: UploadFile = File(...),
    riderPhoto: UploadFile = File(...),
):
    try:
        # Save uploaded files
        aadhar_path = save_file(aadharFile)
        pan_path = save_file(panFile)
        dl_path = save_file(dlFile)
        rider_photo_path = save_file(riderPhoto)

        # Save driver details to MongoDB
        driver_data = {
            "name": name,
            "address": address,
            "aadharNumber": aadharNumber,
            "panNumber": panNumber,
            "dlNumber": dlNumber,
            "vehicle": vehicle,
            "aadharFile": aadhar_path,
            "panFile": pan_path,
            "dlFile": dl_path,
            "riderPhoto": rider_photo_path,
        }

        result = await collection.insert_one(driver_data)
        return {"message": "Driver registered successfully", "id": str(result.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoint to get all drivers
@app.get("/drivers")
async def get_drivers():
    try:
        drivers = await collection.find().to_list(100)
        return drivers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/")
async def root():
    return {"message": "FastAPI File Upload with MongoDB"}

