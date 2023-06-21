from XTBClient.api import XTBClient, MODES, TRANSACTION_TYPE
from time import sleep
import os
from utility import utility

# client = XTBClient()
# client.login(os.environ.get("XTB_login"), os.environ.get("XTB_pass"))
# retval = client.login(
    # os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
# )

# retval = client.send_command("getProfits", streamSessionId=retval)
# client.send_command("getBalance", streamSessionId="8469308861804289383")
# retval = client.get_trades()

# retval = client.open_transaction(
#     MODES.SELL, "EURUSD", 0.5, sl=2, tp=2
# )

# retval = client.get_trades()

# retval = client.close_all()

# retval = client.transaction(
#     MODES.BUY,
#     "EURUSD",
#     TRANSACTION_TYPE.CLOSE,
#     0.01,
#     order=518659615,
#     price=1.08378,
# )

# client.logout()

utility.blockPrint()
print("hi")
utility.enablePrint()
print("hi")