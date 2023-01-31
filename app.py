import os
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()

app = Flask(__name__)

@app.get("/api/healthz")
def get_healthz():
    return {"message ": "Healthy"},200
