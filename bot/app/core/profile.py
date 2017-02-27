import app


def save_currency_preference(uid, currency='SGD'):
    redis = app.get_redis()
    redis.set("currency_%s" % uid, currency)


def get_currency_preference(uid):
    redis = app.get_redis()
    data = redis.get("currency_%s" % uid)
    if data is None:
        return 'SGD'
    return data
