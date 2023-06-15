from XTBClient.api import XTBClient, MODES, TRANSACTION_TYPE
from time import sleep
import os

client = XTBClient()
# client.login(os.environ.get("XTB_login"), os.environ.get("XTB_pass"))
client.login(14850296, os.environ.get("XTB_pass"))

retval = client.get_trades()

retval = client.transaction(
    MODES.SELL, "EURUSD", TRANSACTION_TYPE.OPEN, 0.5
)

retval = client.get_trades()

retval = client.close_transaction(retval[0])

# retval = client.transaction(
#     MODES.BUY,
#     "EURUSD",
#     TRANSACTION_TYPE.CLOSE,
#     0.01,
#     order=518659615,
#     price=1.08378,
# )

client.logout()
