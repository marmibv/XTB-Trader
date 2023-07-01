from XTBClient.api import XTBClient, MODES
from utility import utility
import os


logger = utility.KLogger(__name__, filename=".commander_log")


class APICommander:
    def login(func):
        def function_wrapper(self):
            client = XTBClient()
            client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            func(self, client)
            client.logout()

        return function_wrapper

    @login
    def open_transaction(self, client):
        try:
            mode = (
                MODES.BUY
                if input("Buy/Sell: ").lower() == "buy"
                else MODES.SELL
            )
            symbol = input("Symbol: ").upper()
            volume = float(input("Volume: "))
            sl = int(input("Stop loss: "))
            tp = int(input("Take profit: "))
            result = client.open_transaction(
                mode, symbol, volume, sl=sl, tp=tp
            )
            result["theme"] = "NEW BUY" if mode == MODES.BUY else "NEW SELL"
            logger.report(result)
        except Exception as e:
            print("Entered Except")
            logger.err(str(e))

    @login
    def close_all(self, client):
        try:
            result = client.close_all()
            result["theme"] = "CLOSE ALL"
            logger.report(result)
        except Exception as e:
            print("Entered Except")
            logger.err(str(e))

    @login
    def get_all_symbols(self, client):
        try:
            result = client.get_all_symbols()
            logger.report(str(result))
        except Exception as e:
            print("Entered Except")
            logger.err(str(e))


functions = [fun for fun in dir(APICommander) if not fun.startswith("_")]
functions.pop([idx for idx, s in enumerate(functions) if "login" in s][0])

commander = APICommander()


for index, test in enumerate(functions):
    print("{}. {}".format(index, test))

choice = int(input())

try:
    while True:
        os.system("clear")
        getattr(commander, functions[choice])()
        input()
except KeyboardInterrupt:
    print("Finished")
