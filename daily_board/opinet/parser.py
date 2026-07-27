from daily_board.opinet.errors import OpinetError


def normalize_oil_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def find_station_record(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise OpinetError("오피넷 응답의 최상위 값이 객체가 아닙니다.")
    result = payload.get("RESULT", payload)
    if isinstance(result, dict):
        oil = result.get("OIL")
        if isinstance(oil, list):
            for item in oil:
                if isinstance(item, dict):
                    return item
        if isinstance(oil, dict):
            return oil
        message = result.get("MESSAGE") or result.get("MSG") or result.get("message")
        if message:
            raise OpinetError(str(message))
        if "OS_NM" in result or "UNI_ID" in result:
            return result
    raise OpinetError("오피넷 응답에서 주유소 상세정보를 찾지 못했습니다.")


def parse_price(value):
    if value is None:
        return None
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return int(number) if number.is_integer() else number
