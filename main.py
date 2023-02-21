import json
import shutil
import subprocess

from bson import ObjectId
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import motor.motor_asyncio
from kafka import KafkaProducer

from models import FlightReport

app = FastAPI()

client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://user:pass@localhost:27017')
db = client['flight-reports']

producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

origins = [
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/", response_model=FlightReport)
async def upload_file(images: list[UploadFile] = File(...)):
    for image in images:
        with open(f'upload/${image.filename}', "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    flight = {'path_to_images': 'uploads'}
    new_flight = await db["flight-reports"].insert_one(flight)

    created_flight = await db["flight-reports"].find_one({"_id": new_flight.inserted_id})
    producer.send('orthomosaic', {'id': str(new_flight.inserted_id)})

    return created_flight


@app.get("/{flight_id}")
async def upload_file(flight_id: str):
    flight = await db["flight-reports"].find_one({"_id": ObjectId(flight_id)})

    return JSONResponse(status_code=200, content=flight['orthomosaic_progress'])
