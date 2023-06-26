import pandas as pd
import logging
from datetime import datetime
import enum
import time
import json
import yfinance as yf
from .exceptions import NotLogged, SocketError, CommandFailed
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


def _get_data(command, **parameters):
    data = {
        "command": command,
    }
    if parameters:
        data["arguments"] = {}
        for key, value in parameters.items():
            data["arguments"][key] = value
    return data


class XTBClient:
    def __init__(self):
        self._login_data = None
        self._time_last_request = time.time() - MAX_TIME_INTERVAL
        self.status = STATUS.NOT_LOGGED
        self.ws = None
        self.trades = {}

    def login(self, user_id: int, password: str, mode="demo"):
        """login command"""
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

    def logout(self):
        """logout command"""
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
        except Exception as e:
            self.login(self._login_data[0], self._login_data[1])
            return func(*args, **kwargs)

    def _send_command(self, command, **kwargs):
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

    def send_command(self, command, **kwargs):
        """with check login"""
        return self._login_decorator(self._send_command, command, **kwargs)

    def _transaction(
        self,
        mode: MODES,
        symbol: str,
        trans_type: TRANSACTION_TYPE,
        volume: float,
        **kwargs,
    ):
        """Creates a new transaction"""
        try:
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

            status["request_status"] = TRANSACTION_STATUS(
                status["requestStatus"]
            )

            del status["requestStatus"]

        except Exception as e:
            status = dict(request_status=TRANSACTION_STATUS(0), message=str(e))

        return status

    # Usable requests
    def check_if_market_open(self, list_of_symbols: list):
        """Checks if market is open at the moment"""
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
        as_df=True,
    ):
        """Returns candles in given timeframe for given symbol"""
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

        if as_df:
            df = pd.DataFrame(candle_history)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

            df.set_index("timestamp", inplace=True)

        return df if as_df else candle_history

    def get_all_symbols(self):
        """Returns information about all symbols available in XTB"""
        return self.send_command("getAllSymbols")

    def get_symbol(self, symbol: str):
        """Returns information about a specified symbol"""
        return self.send_command("getSymbol", symbol=symbol)

    def open_transaction(
        self,
        mode: MODES,
        symbol: str,
        volume: float,
        **kwargs,
    ):
        """Open transaction wrapper"""
        return self._transaction(
            mode, symbol, TRANSACTION_TYPE.OPEN, volume, **kwargs
        )

    def close_transaction(self, trade: TRANSACTION):
        """Closes a trade"""
        response = self._transaction(
            MODES.BUY,
            trade.symbol,
            TRANSACTION_TYPE.CLOSE,
            trade.volume,
            order=trade.order,
            price=trade.price,
        )
        return response

    def close_all(self):
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

    def transaction_status(self, order_id: int):
        """Returns information about a transaction"""
        return self.send_command("tradeTransactionStatus", order=int(order_id))

    def get_trades(self):
        """Gets all user trades"""
        return [
            TRANSACTION(**t)
            for t in self.send_command("getTrades", openedOnly=True)
        ]

    def update_trades(self):
        """Gets all user trades and adds them to client variable"""
        self.trades = {str(t.order): t for t in self.get_trades()}

    def get_ticks(self, symbols: list):
        """Gets ticks for specified symbols"""
        return self.send_command(
            "getTickPrices",
            level=0,
            symbols=symbols,
            timestamp=datetime.now().timestamp(),
        )

    def get_profits(self):
        self.update_trades()
        suma = 0
        for trade in list(self.trades.values()):
            suma += trade.profit

        return suma


class YahooClient:
    def __init__(self):
        return None

    def get_candles_for_period(
        self, start: datetime, end: datetime, symbol="EURUSD=X"
    ) -> pd.DataFrame:
        return yf.download(
            symbol,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
        )
