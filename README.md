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

