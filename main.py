from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
# Routes will be dynamically added here

from app.auth.routes import router as auth_router
from app.script.routes import router as script_router
from app.product.routes import router as product_router
from app.developer.routes import router as developer_router
from app.admin_email.routes import router as admin_router
from dotenv import dotenv_values
from pymongo import MongoClient
from app.script.scheduler import initialize_schedules

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from your frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)
# app.include_router(auth_router,tags=["Auth"], prefix='/auth')
# app.include_router(product_router, tags=["Product"],prefix='/product') 
config = dotenv_values(".env")

@app.on_event("startup")
def startup_db_client():
    # app.mongodb_client = MongoClient("mongodb://localhost:27017")
    # app.mongodb_client = MongoClient("mongodb+srv://bidsinfoglobal:3N4ZRDaS6H64GajL@qa.t5cmca1.mongodb.net")
    MONGO_URI = config["MONGODB_CONNECTION_URI"]
    DATABASE_NAME = config["DB_NAME"]
    app.mongodb_client = MongoClient(MONGO_URI)
    app.database = app.mongodb_client[DATABASE_NAME]
    print("Connected to the MongoDB database!")

    #Initialize scheduler in a separate thread
    print("[INFO] Initializing scheduled jobs in a separate thread...")
    thread = threading.Thread(target=initialize_schedules, args=(app.database,))
    thread.daemon = True  # Ensures thread exits when the main program terminates
    thread.start()
    print("[INFO] Scheduled jobs are being initialized in the background.")
    print("[INFO] Scheduled jobs initialized successfully.")


@app.on_event("shutdown")
def shutdown_db_client():
    app.mongodb_client.close()


app.include_router(admin_router, tags=["Admin"],prefix="/admin")
app.include_router(developer_router,tags=["Developer"], prefix='/developer')
app.include_router(script_router,tags=["Script"], prefix='/script')