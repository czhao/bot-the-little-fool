## System Design

This is an attempt to build a bot backend with Flask stack. Currently it supports Facebook messenger only.

- receive the message via webhook
- use `supervisor` to perform asynchrous processing to comply with guideline from Facebook
- use `celery` for task dispatch

## Features
- bill management

## Setup

use virtual environment

```
virtualenv venv
source venv/bin/activate
```

## Installation
```
pip install flask
pip install hashlib
pip install requests
pip install raven
pip install blinker
pip install python-memcached
pip install redis
pip install supervisor
```

## Run the bot
```
cd bot
pip install --editable .
export FLASK_APP=bot
export BOT_APPLICATION_SETTINGS='ABOSOLUTE_PATH/bot_config.cfg'
flask run
```

sample configuration
```
DEBUG = True
FB_ACCESS_TOKEN = '' 
FB_VERIFY_TOKEN = '1234567'
FB_APP_SECRET_KEY = ''
SENTRY_DSN = ''
```

start memcached locally
```
memcached
```

start redis locally
```
redis-server --port 12094
```

start the celery
```
celery -A bot.bot.celery worker -l info
```

load the database schema
```
sqlite3 bot.db < schema.sql
```




