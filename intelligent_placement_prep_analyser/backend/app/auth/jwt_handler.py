
from jose import jwt
from datetime import datetime,timedelta
from app.config.settings import settings

def create_token(user_id):
    payload={
        "user_id":user_id,
        "exp":datetime.utcnow()+timedelta(hours=6)
    }
    return jwt.encode(payload,settings.JWT_SECRET,algorithm="HS256")
