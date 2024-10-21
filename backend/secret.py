# from app import create_app
# from extensions import db
# from models import User

# # Create the Flask application
# app = create_app()

# with app.app_context():
#     # Delete all users
#     User.query.delete()

#     # Commit the changes
#     db.session.commit()
#     print("All users have been deleted.")

# import openai

# # Set up your OpenAI API key
# openai.api_key = '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'
# # Generate an image using DALL-E
# response = openai.Image.create(
#   prompt="Design a simple and unique logo for an educational platform with abstract book and brain symbols.",
#   n=1,
#   size="1024x1024"
# )

# # Get the URL of the generated image
# image_url = response['data'][0]['url']
# print(image_url)
import requests
import cbor2
import base64

CANISTER_URL = 'http://127.0.0.1:8000'
CANISTER_ID = 'bkyz2-fmaaa-aaaaa-qaaaq-cai'
PRINCIPAL_ID = 'liuhg-7ksvc-vcx33-msiv2-4foxl-c7u2q-bvycu-5jpmp-3bwgo-gydyg-5ae'

# Function to decode principal ID (we'll stick to this one as it's in base32)
def decode_principal_id(encoded_id):
    encoded_str = encoded_id.replace('-', '').upper()
    decoded_bytes = base64.b32decode(encoded_str + '=' * ((8 - len(encoded_str) % 8) % 8))
    
    if len(decoded_bytes) != 29:
        raise ValueError(f"Principal ID must be exactly 29 bytes long, got {len(decoded_bytes)} bytes")
    
    return decoded_bytes

try:
    principal_id_bytes = decode_principal_id(PRINCIPAL_ID)
except Exception as e:
    print(f"Error converting Principal ID: {e}")
    raise

# Create the CBOR-encoded method arguments
args = {
    "id": 1,
    "username": "kamswbeshwswqswinfa",
    "email": "d@wgwswjsexmawdil.com"
}

# Prepare the content payload
content = {
    "request_type": "call",
    "canister_id": CANISTER_ID,
    "method_name": "createUser",
    "sender": principal_id_bytes,
    "ingress_expiry": 0,
    "arg": cbor2.dumps(args)
}

# Serialize the entire request payload into CBOR
cbor_request_payload = cbor2.dumps(content)

headers = {
    "Content-Type": "application/cbor"
}

# Send the POST request
response = requests.post(f'{CANISTER_URL}/api/v2/canister/{CANISTER_ID}/call', data=cbor_request_payload, headers=headers)

print("Response from canister:", response.content)


headers = {
    "Content-Type": "application/cbor"
}

# Send the POST request
response = requests.post(f'{CANISTER_URL}/api/v2/canis2ter/{CANISTER_ID}/call', data=cbor_request_payload, headers=headers)

print("Response from canister:", response.content)
