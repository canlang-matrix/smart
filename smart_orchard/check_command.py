from app import create_app
from app.models import ControlCommand

app = create_app()

with app.app_context():
    cmd = ControlCommand.query.order_by(ControlCommand.id.desc()).first()
    if cmd:
        print(cmd.id, cmd.device, cmd.command, cmd.status, cmd.created_at, cmd.executed_at)
    else:
        print('no command found')
