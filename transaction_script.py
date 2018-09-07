from app import app
from app.models import User
from app.tasks import transactions_task

import httplib
import traceback
from urllib2 import Request, urlopen

SITE_URL = app.config["SITE_URL"]
try:
    request = Request(SITE_URL)
    ret = urlopen(SITE_URL)
except:
    traceback.print_exc()

for user in User.query.all():
    for team in user.teams:
        ret = transactions_task.delay(team.id)
