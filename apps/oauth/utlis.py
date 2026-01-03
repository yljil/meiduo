from meiduo import settings
from itsdangerous import TimedSerializer as Serializer

def generic_openid(openid):
    # 这个类可以对数据进行加密，还可以添加一个时效
    # secret_key     密钥， expires_in   过期时间(秒)
    s = Serializer(secret_key=settings.SECRET_KEY)
    access_token = s.dumps({'openid': openid})

    #将bytes类型转为str
    return access_token

def check_access_token(token):
    s = Serializer(secret_key=settings.SECRET_KEY)
    try:
        to = s.loads(token)
    except Exception:
        return None
    else:
        return to.get('openid')
