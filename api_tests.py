from XTBClient.api import XTBClient
from XTBClient.enums import MODES
import os


class APITests:
    def test(func):
        def function_wrapper(self):
            print("---------------------------------------------------")
            print("Function: " + func.__name__)
            input()
            func(self)
            print("---------------------------------------------------\n\n")

        return function_wrapper

    @test
    def incorrect_login(self):
        client = XTBClient()
        try:
            result = client.login(os.environ.get("XTB_user_num"), "12345")
            print("Result: " + str(result))
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @test
    def incorrect_logout(self):
        client = XTBClient()
        try:
            result = client.logout()
            print("Result: " + str(result))
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @test
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

    @test
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

    @test
    def correct_open_transaction_no_sl_tp(self):
        client = XTBClient()
        try:
            client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            result = client.open_transaction(MODES.BUY, "EURUSD", 0.01)
            print("Result: " + str(result))
            client.logout()
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @test
    def correct_open_transaction_with_sl_tp(self):
        client = XTBClient()
        try:
            client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            result = client.open_transaction(
                MODES.BUY, "EURUSD", 0.01, sl=1, tp=1
            )
            print("Result: " + str(result))
            client.logout()
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @test
    def incorrect_open_transaction_no_sl_tp(self):
        client = XTBClient()
        try:
            client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            result = client.open_transaction(MODES.BUY, "EURUSD", 1.1)
            print("Result: " + str(result))
            client.logout()
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @test
    def incorrect_open_transaction_with_sl_tp(self):
        client = XTBClient()
        try:
            client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            result = client.open_transaction(
                MODES.BUY, "EURUSD", 0.01, sl=100, tp=200
            )
            print("Result: " + str(result))
            client.logout()
        except Exception as e:
            print("Entered Except")
            print(str(e))

    @test
    def close_all(self):
        client = XTBClient()
        try:
            client.login(
                os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
            )
            result = client.close_all()
            print("Result: " + str(result))
            client.logout()
        except Exception as e:
            print("Entered Except")
            print(str(e))


tests = [fun for fun in dir(APITests) if not fun.startswith("_")]

tester = APITests()


for index, test in enumerate(tests):
    print("{}. {}".format(index, test))
print("{}. {}".format(len(tests), "all"))

choice = int(input())

if choice == len(tests):
    for test in tests:
        os.system("clear")
        getattr(tester, test)()
        input()
else:
    os.system("clear")
    getattr(tester, tests[choice])()
    input()
