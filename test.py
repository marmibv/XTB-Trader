from XTBClient.api import XTBClient, MODES
from XTBClient import exceptions
import os

# Incorrect login ------------------------------------------------------------
input("Incorrect login:")
client = XTBClient()
try:
    login_result = client.login(os.environ.get("XTB_user_num"), "12345")
except Exception as e:
    print(str(e))

print("Done")

# Incorrect logout -----------------------------------------------------------
input("Incorrect logout")
try:
    client.logout()
except Exception as e:
    print(str(e))
print("Done")

# Incorrect login + logout ---------------------------------------------------
input("Incorrect login + logout:")
client = XTBClient()
try:
    login_result = client.login(os.environ.get("XTB_user_num"), "12345")
    client.logout()
except Exception as e:
    print(str(e))
print("Done")


# Correct login -------------------------------------------------------------
input("Correct login:")
client = XTBClient()
login_result = client.login(
    os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
)
client.logout()
print("Done")

# Correct Open Transaction no SL or TP -------------------------------------
input("Open transaction normal, no SL or TP:")
client = XTBClient()
login_result = client.login(
    os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
)
retval = client.open_transaction(MODES.BUY, "BTC-USD", 0.01)
client.logout()
print("Done")


# Correct Open Transaction with SL and TP ---------------------------------
input("Open transaction normal, with SL and TP:")
client = XTBClient()
login_result = client.login(
    os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
)
retval = client.open_transaction(MODES.BUY, "BTC-USD", 0.01, sl=1, tp=1)
client.logout()
print("Done")


# Incorrect Open Transaction no SL or TP ---------------------------------
input("Open transaction incorrect, no SL or TP:")
client = XTBClient()
login_result = client.login(
    os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
)
retval = client.open_transaction(MODES.BUY, "BTC-USD", 1.1)
client.logout()
print("Done")

# Incorrect Open Transaction with SL and TP ---------------------------------
input("Open transaction incorrect, wrong SL or TP:")
client = XTBClient()
login_result = client.login(
    os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
)
retval = client.open_transaction(MODES.BUY, "BTC-USD", 0.01, sl=100, tp=200)
client.logout()
print("Done")
