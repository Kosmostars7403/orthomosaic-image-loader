import json
import os
import shutil
from datetime import datetime

from bson import ObjectId
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import motor.motor_asyncio
from kafka import KafkaProducer
from exif import Image

from models import FlightReport
from utils import is_image

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
async def upload_file(body=Form(...), images: list[UploadFile] = File(...)):
    body = json.loads(body)

    is_date_extracted = False
    flight_date = datetime.today()

    for image in images:
        if not is_image(image.filename):
            continue

        if not is_date_extracted:
            exif_meta = Image(image.file)

            if exif_meta.has_exif:
                flight_date = datetime.strptime(exif_meta['datetime'], '%Y:%m:%d %H:%M:%S')

            if not os.path.exists(f'upload/{flight_date}'):
                os.makedirs(f'upload/{flight_date}')

            is_date_extracted = True

        with open(f'upload/{flight_date}/{image.filename}', "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    flight = {
        'path_to_images': '/Users/ivancernakov/Documents/GitHub/orthomosaic-image-loader/upload',
        'type': body['flightType'],
        'flight_date': flight_date or None
    }

    new_flight = await db["flight-reports"].insert_one(flight)
    created_flight = await db["flight-reports"].find_one({"_id": new_flight.inserted_id})
    producer.send('orthomosaic', {
        'id': str(new_flight.inserted_id),
        'image_folder': f'/Users/ivancernakov/Documents/GitHub/orthomosaic-image-loader/upload/{flight_date}'
    })

    return created_flight


@app.get("/{flight_id}")
async def upload_file(flight_id: str):
    flight = await db["flight-reports"].find_one({"_id": ObjectId(flight_id)})

    if 'orthomosaic_progress' not in flight:
        return JSONResponse(status_code=200, content={'status': 'PROCESSING'})

    return JSONResponse(status_code=200, content=flight['orthomosaic_progress'])
