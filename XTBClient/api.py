from XTBApi.api import Client
import mplfinance as mpf
import pandas as pd
import logging
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import enum
import time
import json
import yfinance as yf
from .exceptions import NotLogged, SocketError, CommandFailed
from websocket import create_connection
from websocket._exceptions import WebSocketConnectionClosedException


LOGIN_TIMEOUT = 120
MAX_TIME_INTERVAL = 0.200
LOGGER = logging.getLogger("XTBApi.api")
LOGGER.setLevel(logging.INFO)


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
        self.LOGGER = logging.getLogger("XTBApi.api.BaseClient")

    def login(self, user_id, password, mode="demo"):
        """login command"""
        self.ws = create_connection(f"wss://ws.xtb.com/{mode}")
        response = self._send_command(
            "login", userId=user_id, password=password
        )
        self._login_data = (user_id, password)
        self.status = STATUS.LOGGED
        self.LOGGER.info("CMD: login...")
        return response

    def logout(self):
        """logout command"""
        response = self._send_command("logout")
        self.status = STATUS.LOGGED
        self.LOGGER.info("CMD: logout...")
        return response

    def _login_decorator(self, func, *args, **kwargs):
        if self.status == STATUS.NOT_LOGGED:
            raise NotLogged()
        try:
            return func(*args, **kwargs)
        except SocketError:
            LOGGER.info("re-logging in due to LOGIN_TIMEOUT gone")
            self.login(self._login_data[0], self._login_data[1])
            return func(*args, **kwargs)
        except Exception as e:
            LOGGER.warning(e)
            self.login(self._login_data[0], self._login_data[1])
            return func(*args, **kwargs)

    def _send_command(self, command, **kwargs):
        dict_data = _get_data(command, **kwargs)

        time_interval = time.time() - self._time_last_request
        # self.LOGGER.debug("took {} s.".format(time_interval))
        if time_interval < MAX_TIME_INTERVAL:
            time.sleep(MAX_TIME_INTERVAL - time_interval)
        try:
            self.ws.send(json.dumps(dict_data))
            response = self.ws.recv()
        except WebSocketConnectionClosedException:
            raise SocketError()
        self._time_last_request = time.time()
        res = json.loads(response)
        if res["status"] is False:
            self.LOGGER.info(f"CMD {command} with {dict_data}: FAILED")
            raise CommandFailed(res)
        if "returnData" in res.keys():
            self.LOGGER.info(f"CMD {command} with {dict_data}: done")
            self.LOGGER.debug(res["returnData"])
            return res["returnData"]

    def send_command(self, command, **kwargs):
        """with check login"""
        return self._login_decorator(self._send_command, command, **kwargs)

    def get_trading_hours(self, trade_position_list):
        """getTradingHours command"""
        self.LOGGER.info(
            f"CMD: get trading hours of len " f"{len(trade_position_list)}..."
        )
        response = self.send_command(
            "getTradingHours", symbols=trade_position_list
        )

        for symbol in response:
            for day in symbol["trading"]:
                day["fromT"] = int(day["fromT"] / 1000)
                day["toT"] = int(day["toT"] / 1000)
            for day in symbol["quotes"]:
                day["fromT"] = int(day["fromT"] / 1000)
                day["toT"] = int(day["toT"] / 1000)
        return response

    # Usable requests
    def check_if_market_open(self, list_of_symbols):
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
        return self.send_command("getAllSymbols")

    def get_symbol(self, symbol):
        self.LOGGER.info(f"CMD: get symbol {symbol}...")
        return self.send_command("getSymbol", symbol=symbol)

    def open_transaction(self, mode, symbol, volume, sl=0, tp=0, message=""):
        symbol_info = self.get_symbol(symbol)
        price = symbol_info["ask" if mode.value == 0 else "bid"]
        return self.send_command(
            "tradeTransaction",
            tradeTransInfo={
                "cmd": mode.value,
                "comment": message,
                "ie_deviation": 0,
                "order": 0,
                "price": price,
                "sl": price - sl*0.0001,
                "symbol": symbol,
                "tp": price + tp*0.0001,
                "type": 0,
                "volume": volume,
            },
        )

    def transaction_status(self, order_id):
        return self.send_command("tradeTransactionStatus", order=int(order_id))

    def get_trades(self):
        return self.send_command("getTrades", openedOnly=True)

    def get_ticks(self, symbols):
        return self.send_command(
            "getTickPrices",
            level=0,
            symbols=symbols,
            timestamp=datetime.now().timestamp(),
        )


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
