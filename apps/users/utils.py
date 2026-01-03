from itsdangerous import TimedSerializer as Serializer
from meiduo import settings

def generate_token(user_id): #加密
    s = Serializer(settings.SECRET_KEY)
    data = s.dumps({'user_id': user_id})
    return data

def check_token(token):
    s = Serializer(settings.SECRET_KEY)
    try:
        result = s.loads(token)
    except Exception as e:
        return None
    return result.get('user_id')