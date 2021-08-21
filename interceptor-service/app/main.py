import uuid
import json
import logging
import requests

from logging.config import dictConfig
from .logger import LogConfig
from datetime import datetime

from pydantic import BaseModel
from fastapi import ( 
    Response,
    Request,
    FastAPI, 
    Depends
)

dictConfig(LogConfig().dict())
logger = logging.getLogger("custom-log")

app = FastAPI(
    title="Interceptor Service",
    description="Dispatcher service for Internal App - Odoo",
    version="1.0",
)

odoo_key = "Bearer ABC"
odoo_url = "http://host.docker.internal:9000/order/"
odoo_headers = {
    "Content-Type": "application/json",
    "Authorization": odoo_key
}

access_key = "Bearer XYZ"


def authentication(req: Request):
    client_key = req.headers["Authorization"]
    if client_key != access_key:
        return False
    return True

def message(data={}):
    try:
        message_id = (uuid.uuid4().hex).upper()
        payload = data.get('payload')
        event = data.get('event')
        now = str(datetime.now())

        message = {
            "message_id" : message_id,
            "timestamp" : now,
            "event" : event,
            "payload" : payload
        }
        logger.info(f"message received: {json.dumps(message)}")
    except:
        logger.error(f"invalid message format: {data}")

@app.get("/")
def root ():
  return {"Service is running ..."}

@app.post("/order", status_code=200)
async def action_create_order(
        req: Request,
        response: Response, 
        authorized: bool = Depends(authentication)
    ):
    res = {}

    if authorized:
        try:
            data = await req.json()
            request = requests.post(odoo_url, headers=odoo_headers, data=json.dumps(data))

            response.status_code = request.status_code
            res = request.json()
        except:
            response.status_code = 500
            res = {
                "success": False,
                "message": "Internal Server Error"
            }
    else:
        response.status_code = 401
        res = {
                "success": False,
                "message": "Token Not Found"
              }
    return res

@app.get("/order/{order_id}", status_code=200)
async def action_read_order(
        order_id: int, 
        response: Response, 
        authorized: bool = Depends(authentication)
    ):

    url = odoo_url + str(order_id)
    res = {}

    if authorized:
        try:
            req = requests.get(url, headers=odoo_headers)

            response.status_code = req.status_code
            res = req.json()
        except:
            response.status_code = 500
            res = {
                "success": False,
                "message": "Internal Server Error"
            }
    else:
        response.status_code = 401
        res = {
                "success": False,
                "message": "Token Not Found"
              }
    return res

@app.put("/order/{order_id}", status_code=200)
async def action_update_order(
        req: Request,
        order_id: int, 
        response: Response, 
        authorized: bool = Depends(authentication)
    ):
    res = {}
    url = odoo_url + str(order_id)

    if authorized:
        try:
            data = await req.json()
            request = requests.put(url, headers=odoo_headers, data=json.dumps(data))

            response.status_code = request.status_code
            res = request.json()
        except:
            response.status_code = 500
            res = {
                "success": False,
                "message": "Internal Server Error"
            }
    else:
        response.status_code = 401
        res = {
                "success": False,
                "message": "Token Not Found"
              }
    return res

@app.post("/webhook", status_code=200)
async def webhook(
        data: dict,
        request: Request,
        response: Response, 
        authorized: bool = Depends(authentication)
    ):
    logger.info("webhook authorization check")
    if authorized:
        logger.info("webhook authorized publisher")
        message(data)
    else:
        logger.error("webhook unauthorized publisher")
    return {"result": "Ok"}
