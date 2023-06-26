from XTBClient.api import XTBClient, MODES
import os


class APITests:
    def label(func):
        def function_wrapper(self):
            print("---------------------------------------------------")
            print("Function: " + func.__name__)
            input()
            func(self)
            print("---------------------------------------------------\n\n")

        return function_wrapper

    @label
    def incorrect_login(self):
        client = XTBClient()
        try:
            result = client.login(os.environ.get("XTB_user_num"), "12345")
            print("Result: " + str(result))
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @label
    def incorrect_logout(self):
        client = XTBClient()
        try:
            result = client.logout()
            print("Result: " + str(result))
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @label
    def incorrect_login_logout(self):
        client = XTBClient()
        try:
            result = client.login(os.environ.get("XTB_user_num"), "12345")
            print("Result: " + str(result))
            result = client.logout()
            print("Result: " + str(result))
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @label
    def correct_login(self):
        try:
            client = XTBClient()
            result = client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            print("Result: " + str(result))
            result = client.logout()
            print("Result: " + str(result))
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @label
    def correct_open_transaction_no_sl_tp(self):
        client = XTBClient()
        try:
            client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            result = client.open_transaction(MODES.BUY, "BTC-USD", 0.01)
            print("Result: " + str(result))
            client.logout()
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @label
    def correct_open_transaction_with_sl_tp(self):
        client = XTBClient()
        try:
            client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            result = client.open_transaction(
                MODES.BUY, "BTC-USD", 0.01, sl=1, tp=1
            )
            print("Result: " + str(result))
            client.logout()
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @label
    def incorrect_open_transaction_no_sl_tp(self):
        client = XTBClient()
        try:
            client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            result = client.open_transaction(MODES.BUY, "BTC-USD", 1.1)
            print("Result: " + str(result))
            client.logout()
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @label
    def incorrect_open_transaction_with_sl_tp(self):
        client = XTBClient()
        try:
            client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            result = client.open_transaction(
                MODES.BUY, "BTC-USD", 0.01, sl=100, tp=200
            )
            print("Result: " + str(result))
            client.logout()
        except Exception as e:
            print("Entered Except")
            print(str(e))


tests = [fun for fun in dir(APITests) if not fun.startswith("_")]

tester = APITests()

for test in tests:
    getattr(tester, test)()
