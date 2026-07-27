import json

from daily_board.constants import OPINET_CONFIG_FILE
from daily_board.paths import opinet_config_path


def load_opinet_config() -> dict:
    config_path = opinet_config_path()
    if not config_path.is_file():
        raise FileNotFoundError(
            f"{OPINET_CONFIG_FILE} 파일을 찾을 수 없습니다.\n"
            f"파일 위치: {config_path}\n"
            f"{OPINET_CONFIG_FILE}을 DailyBoard.exe와 같은 폴더에 두세요."
        )
    try:
        with config_path.open("r", encoding="utf-8-sig") as file:
            config = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{OPINET_CONFIG_FILE} JSON 형식이 올바르지 않습니다. "
            f"(줄 {error.lineno}, 열 {error.colno})"
        ) from error
    if not isinstance(config, dict):
        raise ValueError(f"{OPINET_CONFIG_FILE}의 최상위 값은 JSON 객체여야 합니다.")
    code = config.get("code")
    if not isinstance(code, str) or not code.strip():
        raise ValueError(f"{OPINET_CONFIG_FILE}에 유효한 code 값이 없습니다.")
    normalized = {"code": code.strip()}
    for group_name in ("favorites", "highway"):
        raw_ids = config.get(group_name, [])
        if raw_ids is None:
            raw_ids = []
        if not isinstance(raw_ids, list):
            raise ValueError(f"{OPINET_CONFIG_FILE}의 {group_name} 값은 배열이어야 합니다.")
        station_ids = []
        seen = set()
        for value in raw_ids:
            if not isinstance(value, str):
                continue
            station_id = value.strip()
            if station_id and station_id not in seen:
                seen.add(station_id)
                station_ids.append(station_id)
        normalized[group_name] = station_ids
    return normalized
