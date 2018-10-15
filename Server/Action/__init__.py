from Server.Action.common_api import common_api_blueprint
from Server.Action.account import account_blueprint

blueprints = [
    common_api_blueprint,
    account_blueprint,
]
