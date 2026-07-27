import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from daily_board.constants import OPINET_MAX_WORKERS, PRODUCT_NAMES
from daily_board.opinet.client import fetch_station_detail
from daily_board.opinet.config import load_opinet_config


def fetch_group(group_name: str, station_ids: list[str], api_code: str) -> list[dict]:
    if not station_ids:
        return []
    indexed_results = [None] * len(station_ids)
    worker_count = min(OPINET_MAX_WORKERS, max(1, len(station_ids)))
    with ThreadPoolExecutor(
        max_workers=worker_count,
        thread_name_prefix=f"Opinet-{group_name}",
    ) as executor:
        futures = {
            executor.submit(fetch_station_detail, api_code, station_id): (index, station_id)
            for index, station_id in enumerate(station_ids)
        }
        for future in as_completed(futures):
            index, station_id = futures[future]
            try:
                indexed_results[index] = future.result()
            except Exception as error:
                indexed_results[index] = {
                    "id": station_id,
                    "name": station_id,
                    "brandCode": None,
                    "address": None,
                    "prices": {
                        code: {
                            "productCode": code,
                            "productName": name,
                            "price": None,
                            "tradeDate": None,
                            "tradeTime": None,
                        }
                        for code, name in PRODUCT_NAMES.items()
                    },
                    "error": str(error),
                }
    return indexed_results


def build_opinet_response() -> dict:
    config = load_opinet_config()
    api_code = config["code"]
    groups = {}
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="OpinetGroup") as executor:
        future_map = {
            executor.submit(fetch_group, "favorites", config["favorites"], api_code): "favorites",
            executor.submit(fetch_group, "highway", config["highway"], api_code): "highway",
        }
        for future in as_completed(future_map):
            group_name = future_map[future]
            groups[group_name] = future.result()
    groups = {
        "favorites": groups.get("favorites", []),
        "highway": groups.get("highway", []),
    }
    failed_count = sum(
        1 for stations in groups.values() for station in stations if station.get("error")
    )
    return {
        "success": True,
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
        "groups": groups,
        "summary": {
            "total": sum(len(items) for items in groups.values()),
            "failed": failed_count,
        },
    }
