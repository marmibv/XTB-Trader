import pandas as pd
from datetime import datetime
import enum
import time
import json
from .exceptions import (
    NotLogged,
    SocketError,
    CommandFailed,
    TransactionRejected,
)
from websocket import create_connection
from websocket._exceptions import (
    WebSocketConnectionClosedException,
    WebSocketAddressException,
)


LOGIN_TIMEOUT = 120
MAX_TIME_INTERVAL = 0.200


class STATUS(enum.Enum):
    LOGGED = enum.auto()
    NOT_LOGGED = enum.auto()


class MODES(enum.Enum):
    BUY = 0
    SELL = 1


class PERIOD(enum.Enum):
    ONE_MINUTE = 1
    FIVE_MINUTES = 5
    FIFTEEN_MINUTES = 15
    THIRTY_MINUTES = 30
    ONE_HOUR = 60
    FOUR_HOURS = 240
    ONE_DAY = 1440
    ONE_WEEK = 10080
    ONE_MONTH = 43200


class TRANSACTION_TYPE(enum.Enum):
    OPEN = 0
    CLOSE = 2


class TRANSACTION_STATUS(enum.Enum):
    ERROR = 0
    PENDING = 1
    REQUOTED = 2
    ACCEPTED = 3
    REJECTED = 4
    PRICED = 5


class TRANSACTION:
    def __init__(
        self,
        order,
        symbol,
        close_price,
        profit,
        volume,
        sl,
        tp,
        *args,
        **kwargs,
    ):
        self.order = order
        self.symbol = symbol
        self.profit = profit
        self.volume = volume
        self.price = close_price
        self.sl = sl
        self.tp = tp


def _get_data(command: str, **parameters) -> dict:
    data = {
        "command": command,
    }
    if parameters:
        data["arguments"] = {}
        for key, value in parameters.items():
            data["arguments"][key] = value
    return data


# The XTBClient class is a client for interacting with the XTB trading
# platform, keeping track of
# login data, request time intervals, status, WebSocket connection, and trades.
class XTBClient:
    def __init__(self) -> None:
        self._login_data = None
        self._time_last_request = time.time() - MAX_TIME_INTERVAL
        self.status = STATUS.NOT_LOGGED
        self.ws = None
        self.trades = {}

    def login(self, user_id: int, password: str, mode: str = "demo") -> dict:
        """The `login` function establishes a WebSocket connection to a server
        and sends a login command with the provided user ID and password.

        Parameters
        ----------
        user_id : int
            The user_id parameter is an integer that represents the user's
            ID or account number.
        password : str
            The `password` parameter is a string that represents the user's
            password for authentication.
        mode : str, optional
            The "mode" parameter is used to specify the mode of the connection.
            It is set to "demo" by default, which means it connects to a demo
            server. However, you can also set it to "real" to connect to a real
            server.

        Returns
        -------
            The login method returns a dictionary.

        """
        try:
            self.ws = create_connection(f"wss://ws.xtb.com/{mode}")
        except WebSocketAddressException:
            raise SocketError("Failed to connect to the server")
        response = self._send_command(
            "login", userId=user_id, password=password
        )
        self._login_data = (user_id, password)
        self.status = STATUS.LOGGED
        return response

    def logout(self) -> dict:
        """The `logout` function sends a command to log out and updates the
        status to "logged".

        Returns
        -------
            The response from the `_send_command` method is being returned.

        """
        response = self._send_command("logout")
        self.status = STATUS.LOGGED
        return response

    def _login_decorator(self, func, *args, **kwargs):
        if self.status == STATUS.NOT_LOGGED:
            raise NotLogged()
        try:
            return func(*args, **kwargs)
        except SocketError:
            self.login(self._login_data[0], self._login_data[1])
            return func(*args, **kwargs)
        except Exception:
            self.login(self._login_data[0], self._login_data[1])
            return func(*args, **kwargs)

    def _send_command(self, command: str, **kwargs) -> dict:
        dict_data = _get_data(command, **kwargs)

        time_interval = time.time() - self._time_last_request
        if time_interval < MAX_TIME_INTERVAL:
            time.sleep(MAX_TIME_INTERVAL - time_interval)
        try:
            self.ws.send(json.dumps(dict_data))
            response = self.ws.recv()
        except WebSocketConnectionClosedException:
            raise SocketError("Connection closed")
        except WebSocketAddressException:
            raise SocketError("Failed to connect to the server")
        except AttributeError:
            raise SocketError("Not connected to the server")

        self._time_last_request = time.time()
        res = json.loads(response)
        if res["status"] is False:
            raise CommandFailed(res)
        if "returnData" in res.keys():
            return res["returnData"]
        if command == "login":
            return res["streamSessionId"]

    def send_command(self, command: str, **kwargs) -> dict:
        """The `send_command` function is a method that sends a
        command and its arguments to a remote server, after logging in.

        Parameters
        ----------
        command : str
            The `command` parameter is a string that represents the
            command to be sent.

        Returns
        -------
            The send_command method is returning a dictionary.

        """
        return self._login_decorator(self._send_command, command, **kwargs)

    def _transaction(
        self,
        mode: MODES,
        symbol: str,
        trans_type: TRANSACTION_TYPE,
        volume: float,
        **kwargs,
    ):
        symbol_info = self.get_symbol(symbol)
        price = symbol_info["ask" if mode.value == 0 else "bid"]

        kwargs["price"] = price

        if "sl" in kwargs:
            kwargs["sl"] = kwargs["price"] - kwargs["sl"] * 0.0001 * (
                -1 * mode.value
            )

        if "tp" in kwargs:
            kwargs["tp"] = kwargs["price"] + kwargs["tp"] * 0.0001 * (
                -1 * mode.value
            )
        # check kwargs
        accepted_values = [
            "order",
            "price",
            "expiration",
            "customComment",
            "offset",
            "sl",
            "tp",
        ]
        assert all([val in accepted_values for val in kwargs.keys()])
        info = {
            "cmd": mode.value,
            "symbol": symbol,
            "type": trans_type.value,
            "volume": volume,
        }
        info.update(kwargs)  # update with kwargs parameters

        order = self.send_command("tradeTransaction", tradeTransInfo=info)

        status = self.transaction_status(order.get("order"))

        status["request_status"] = TRANSACTION_STATUS(status["requestStatus"])

        del status["requestStatus"]

        if status["request_status"] == TRANSACTION_STATUS.REJECTED:
            raise TransactionRejected(status["message"])

        return status

    def check_if_market_open(self, list_of_symbols: list) -> dict:
        """The function `check_if_market_open` checks if the market
        is open for a given list of symbols based on their trading hours.

        Parameters
        ----------
        list_of_symbols : list
            A list of symbols representing different markets or stocks.

        Returns
        -------
            a dictionary with market statuses.

        """
        _td = datetime.today()
        actual_tmsp = _td.hour * 3600 + _td.minute * 60 + _td.second
        response = self.get_trading_hours(list_of_symbols)
        market_values = {}
        for symbol in response:
            today_values = [
                day
                for day in symbol["trading"]
                if day["day"] == _td.isoweekday()
            ][0]
            if today_values["fromT"] <= actual_tmsp <= today_values["toT"]:
                market_values[symbol["symbol"]] = True
            else:
                market_values[symbol["symbol"]] = False
        return market_values

    def get_candles_in_range(
        self,
        symbol: str,
        period: PERIOD,
        start: datetime,
        end=datetime.today(),
    ) -> pd.DataFrame:
        """The `get_candles_in_range` function retrieves candlestick data for
        a specified symbol and time range, and returns it as a pandas
        DataFrame.

        Parameters
        ----------
        symbol : str
            The symbol parameter represents the trading symbol or instrument
            for which you want to retrieve the candlestick data. It could be
            a stock ticker symbol, cryptocurrency symbol, or any other symbol
            used in the trading platform you are working with.
        period : PERIOD
            The `period` parameter represents the time period for which you
            want to retrieve the candlestick data. It is of type `PERIOD`,
            which is likely an enumeration or a custom class that defines
            different time periods such as 1 minute, 5 minutes, 1 hour, etc.
        start : datetime
            The `start` parameter is the starting datetime for the range of
            candles you want to retrieve. It specifies the beginning of the
            time period for which you want to fetch the candle data.
        end
            The `end` parameter is an optional parameter that specifies the
            end date and time for the range of candles to retrieve. If no
            value is provided, it defaults to the current date and time
            (`datetime.today()`).

        Returns
        -------
            The function `get_candles_in_range` returns a pandas DataFrame
            containing candlestick data for a specified symbol, period,
            start, and end time.

        """
        res = self.send_command(
            "getChartRangeRequest",
            info={
                "period": period,
                "start": start.timestamp() * 1000,
                "end": end.timestamp() * 1000,
                "symbol": symbol,
            },
        )

        candle_history = []
        for candle in res["rateInfos"]:
            _pr = candle["open"]
            op_pr = _pr / 10 ** res["digits"]
            cl_pr = (_pr + candle["close"]) / 10 ** res["digits"]
            hg_pr = (_pr + candle["high"]) / 10 ** res["digits"]
            lw_pr = (_pr + candle["low"]) / 10 ** res["digits"]
            new_candle_entry = {
                "timestamp": candle["ctm"] / 1000,
                "open": op_pr,
                "close": cl_pr,
                "high": hg_pr,
                "low": lw_pr,
                "volume": candle["vol"],
            }
            candle_history.append(new_candle_entry)

        df = pd.DataFrame(candle_history)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

        df.set_index("timestamp", inplace=True)

        return df

    def get_all_symbols(self) -> list:
        """The function `get_all_symbols` sends a command to retrieve
        all symbols and returns them as a list.

        Returns
        -------
            a list of symbols with their characteristics.

        """
        return self.send_command("getAllSymbols")

    def get_symbol(self, symbol: str) -> dict:
        """The function `get_symbol` takes a symbol as input and sends
        a command to retrieve information about that symbol.

        Parameters
        ----------
        symbol : str
            The `symbol` parameter is a string that represents
            the symbol you want to retrieve information for.

        Returns
        -------
            a dictionary with information about the symbol.

        """
        return self.send_command("getSymbol", symbol=symbol)

    def open_transaction(
        self, mode: MODES, symbol: str, volume: float, **kwargs
    ) -> dict:
        """The function "open_transaction" is used to open a transaction
        with a specified mode, symbol, volume, and additional keyword
        arguments.

        Parameters
        ----------
        mode : MODES
            The "mode" parameter is of type MODES. It is used to specify
            the mode of the transaction, such as "buy" or "sell".
        symbol : str
            The "symbol" parameter is a string that represents the symbol
            or identifier of the transaction. It is typically used to identify
            a specific asset or security in a financial market.
        volume : float
            The volume parameter represents the quantity or amount of the
            symbol being traded in the
        transaction. It is a float value.

        Returns
        -------
            A dictionary with status of the operation.

        """
        return self._transaction(
            mode, symbol, TRANSACTION_TYPE.OPEN, volume, **kwargs
        )

    def close_all(self) -> dict:
        """The `close_all` function closes all transactions and returns a dictionary with the request status
        and a message indicating the success of the operation.

        Returns
        -------
            a dictionary with two key-value pairs. The first key is "request_status" and the value is the
        constant TRANSACTION_STATUS.ACCEPTED. The second key is "message" and the value is the string "All
        transactions closed successfully."

        """
        self.update_trades()
        for trade in list(self.trades.values()):
            retval = self.close_transaction(trade)
            if retval["request_status"] == TRANSACTION_STATUS.ERROR:
                return retval
        self.update_trades()
        return dict(
            request_status=TRANSACTION_STATUS.ACCEPTED,
            message="All transactions closed successfully.",
        )

    def transaction_status(self, order_id: int) -> dict:
        """The function `transaction_status` sends a command to check the
        status of a trade transaction with a given order ID.

        Parameters
        ----------
        order_id : int
            The `order_id` parameter is an integer that represents the unique
            identifier of a trade transaction.

        Returns
        -------
            Dictionary with transaction status.

        """
        return self.send_command("tradeTransactionStatus", order=int(order_id))

    def get_trades(self) -> list:
        """The function `get_trades` returns a list of `TRANSACTION` objects
        by sending a command to retrieve trades that are currently open.

        Returns
        -------
            The code is returning a list of TRANSACTION objects.

        """
        return [
            TRANSACTION(**t)
            for t in self.send_command("getTrades", openedOnly=True)
        ]

    def update_trades(self) -> None:
        """The function updates the "trades" attribute of an object with
        a dictionary of trades.

        """
        self.trades = {str(t.order): t for t in self.get_trades()}

    def get_ticks(self, symbols: list) -> dict:
        """The function `get_ticks` sends a command to retrieve tick prices
        for a list of symbols, with a specified level and timestamp.

        Parameters
        ----------
        symbols : list
            The `symbols` parameter is a list of symbols for which you
            want to retrieve tick prices. Each symbol represents a
            financial instrument such as a stock, currency pair, or commodity.

        Returns
        -------
            A Dictionary with ticks.


        """
        return self.send_command(
            "getTickPrices",
            level=0,
            symbols=symbols,
            timestamp=datetime.now().timestamp(),
        )

    def get_profits(self) -> float:
        """The function `get_profits` calculates the total
        profit from a list of trades.

        Returns
        -------
            the sum of profits from all trades.

        """
        self.update_trades()
        suma = 0
        for trade in list(self.trades.values()):
            suma += trade.profit
        return suma
