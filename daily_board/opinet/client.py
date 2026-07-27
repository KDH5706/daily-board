import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from daily_board.constants import (
    OPINET_DETAIL_URL,
    OPINET_REQUEST_TIMEOUT_SECONDS,
    PRODUCT_NAMES,
)
from daily_board.opinet.errors import OpinetError
from daily_board.opinet.parser import find_station_record, normalize_oil_list, parse_price


def fetch_station_detail(api_code: str, station_id: str) -> dict:
    query = urlencode({"code": api_code, "id": station_id, "out": "json"})
    request = Request(
        f"{OPINET_DETAIL_URL}?{query}",
        headers={"Accept": "application/json", "User-Agent": "DailyBoard/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=OPINET_REQUEST_TIMEOUT_SECONDS) as response:
            raw_data = response.read()
    except HTTPError as error:
        raise OpinetError(f"오피넷 HTTP 오류: {error.code}") from error
    except URLError as error:
        reason = getattr(error, "reason", error)
        raise OpinetError(f"오피넷 연결 실패: {reason}") from error
    except TimeoutError as error:
        raise OpinetError("오피넷 요청 시간이 초과되었습니다.") from error
    try:
        payload = json.loads(raw_data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OpinetError("오피넷 응답을 JSON으로 해석하지 못했습니다.") from error

    station = find_station_record(payload)
    station_name = str(station.get("OS_NM") or station.get("UNI_ID") or station_id).strip()
    prices = {
        code: {
            "productCode": code,
            "productName": name,
            "price": None,
            "tradeDate": None,
            "tradeTime": None,
        }
        for code, name in PRODUCT_NAMES.items()
    }
    oil_prices = normalize_oil_list(station.get("OIL_PRICE") or station.get("OIL_PRICE_LIST"))
    if len(oil_prices) == 1:
        nested = oil_prices[0].get("OIL")
        if nested is not None:
            oil_prices = normalize_oil_list(nested)
    for oil in oil_prices:
        product_code = str(oil.get("PRODCD", "")).strip()
        if product_code not in prices:
            continue
        prices[product_code] = {
            "productCode": product_code,
            "productName": PRODUCT_NAMES[product_code],
            "price": parse_price(oil.get("PRICE")),
            "tradeDate": oil.get("TRADE_DT"),
            "tradeTime": oil.get("TRADE_TM"),
        }
    return {
        "id": str(station.get("UNI_ID") or station_id),
        "name": station_name,
        "brandCode": station.get("POLL_DIV_CD"),
        "address": station.get("NEW_ADR") or station.get("VAN_ADR"),
        "prices": prices,
    }
