from app.models import User
from app.tasks import transactions_task

for user in User.query.all():
    for team in user.teams:
        ret = transactions_task.delay(team.id)
