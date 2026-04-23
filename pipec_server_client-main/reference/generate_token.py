# get_user_token.py
import os
import time
import jwt
from dotenv import load_dotenv

load_dotenv()

# --- Your Details ---
# Your LiveKit credentials from your .env file
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
# The same room your bot is in
LIVEKIT_ROOM_NAME = os.getenv("LIVEKIT_ROOM_NAME")
# Your name as the participant
HUMAN_PARTICIPANT_NAME = "falcon"
# --- End of Your Details ---

def generate_user_token():
    now = int(time.time())
    payload = {
        'iss': LIVEKIT_API_KEY,
        'sub': HUMAN_PARTICIPANT_NAME,
        'nbf': now,
        'exp': now + 7200, # 2 hours
        'name': HUMAN_PARTICIPANT_NAME,
        'video': {
            'roomJoin': True,
            'room': LIVEKIT_ROOM_NAME,
            'canPublish': True,
            'canSubscribe': True,
        }
    }
    return jwt.encode(payload, LIVEKIT_API_SECRET, algorithm='HS256')

if __name__ == "__main__":
    print("--- Your User Access Token ---")
    print(generate_user_token())
    print("----------------------------")