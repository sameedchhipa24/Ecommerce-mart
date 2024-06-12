from contextlib import asynccontextmanager
import os
import shutil
import uuid
from sqlmodel import SQLModel, Session, create_engine, select
from product_mart import settings
from product_mart.models.products import Product, ProductCreate
from fastapi import Depends, FastAPI, Form, UploadFile, File, HTTPException
from typing import Annotated, List
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
# import logging
# from typing import Annotated, Any, Any, List, Optional
# from fastapi import Depends, FastAPI, HTTPException, Request , status
# from psycopg2 import IntegrityError
# import schedule
# from sqlmodel.ext.asyncio.session import AsyncSession
# import requests
# import time
# from sqlmodel import Session, create_engine
# SANITY_PROJECT_ID = "kthx8xar"
# SANITY_DATASET = "production"
# SANITY_QUERY = '*[_type == "product" ]{_id , name ,description,price,"images": images[0].asset._ref,"slug" :slug.current,_id}'

# def fetch_data_from_sanity():
#     url = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v1/data/query/{SANITY_DATASET}?query={SANITY_QUERY}"
#     response = requests.get(url)
#     print(response)
#     return response.json()['result']




connection_string = str(settings.DATABASE_URL).replace("postgresql", "postgresql+psycopg2")

# Recycle connections after 5 minutes to correspond with the compute scale down
engine = create_engine(connection_string, connect_args={"sslmode": "require"}, pool_recycle=300)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables..")
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Ecommerce Website", version="0.0.1")

# Set up CORS


def get_session():
    with Session(engine) as session:
        yield session


@app.get("/")
def home():
    return {"message": "Hello World"}


# Directory to store images
# Directory to store images
IMAGE_DIR = "./images"

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

@app.post("/products/", response_model=Product)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    slug: str = Form(...),
    files: List[UploadFile] = File(...)
):
    image_paths = []

    for file in files:
        # Generate a unique filename
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(IMAGE_DIR, filename)

        # Save the file to the local filesystem
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_paths.append(file_path)

    # Convert the product to a Product model and add the image paths
    new_product = Product(
        name=name,
        description=description,
        price=price,
        images=",".join(image_paths),  # Concatenate image paths into a single string
        slug=slug,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    # Save the new product to the database
    with Session(engine) as session:
        session.add(new_product)
        session.commit()
        session.refresh(new_product)

    return new_product

@app.delete("/products/{product_id}/")
async def delete_product(product_id: str):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Delete images from the filesystem
        for image_path in product.images.split(","):
            if os.path.exists(image_path):
                os.remove(image_path)

        session.delete(product)
        session.commit()

    return {"message": "Product deleted successfully"}


@app.get("/products/{product_id}/images/")
async def get_product_images(product_id: str):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return {"images": product.images.split(",")}