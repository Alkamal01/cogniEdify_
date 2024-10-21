import requests
import os
import cbor2
import base64
import json

CANISTER_URL = os.getenv('CANISTER_URL', 'http://127.0.0.1:8000')
CANISTER_ID = os.getenv('CANISTER_ID')

def call_canister(method_name, args):
    url = f"{CANISTER_URL}/api/v2/canister/{CANISTER_ID}/call"

    # Correctly serialize the arguments to CBOR, ensuring it is a tuple
    cbor_args = cbor2.dumps([args["id"], args["username"], args["email"]])
    print("Serialized CBOR payload:", cbor_args)  # Debugging

    # Prepare the payload
    payload = {
        "arg": base64.b64encode(cbor_args).decode('utf-8'),
        "method_name": method_name
    }
    headers = {
        "Content-Type": "application/cbor"
    }
    response = requests.post(url, json=payload, headers=headers)

    # Log the raw response
    print("Raw response from canister:", response.content)  # Debugging

    # Handle the response
    try:
        if response.headers.get('Content-Type') == 'application/cbor':
            return cbor2.loads(response.content)
        else:
            return response.json()
    except cbor2.CBORDecodeError:
        print("Failed to decode CBOR. Response content:", response.content)
        return {"status": "invalid CBOR", "response": response.content}



def query_canister(method_name, args):
    url = f"{CANISTER_URL}/api/v2/canister/{CANISTER_ID}/query"
    payload = {
        "method_name": method_name,
        "args": cbor2.dumps(args)  # CBOR encoding
    }
    headers = {
        "Content-Type": "application/cbor"
    }

    response = requests.post(url, data=payload, headers=headers)
    
    try:
        # Check if the response is in CBOR format and decode it
        if response.headers.get('Content-Type') == 'application/cbor':
            return cbor2.loads(response.content)
        else:
            return response.json()
    except (json.JSONDecodeError, cbor2.CBORDecodeError):
        print("Failed to decode the response. Response content:", response.content)
        return {"status": "invalid response", "response": response.content}
