from .parsers.rutubeparser import rutube_posts_and_views_parser
from .parsers.mratingparser import (
    get_rating_data,
    get_socials,
    months_rus,
)
from .parsers.ultimatetgparser import tg_ultimate_parser
from .parsers.commentstgcounter import tg_comments_counter
from .parsers.vkultimateparser import vk_ultimate_parser

from pyrogram import Client
from typing import List, Tuple
import calendar
from datetime import datetime, date

import os
from dotenv import load_dotenv

load_dotenv()

vk_access_token = os.environ.get("VK_ACCESS_TOKEN")


def get_month_range(start_date: date, end_date: date, year: int) -> Tuple[int, int]:
    if year == start_date.year == end_date.year:
        return start_date.month, end_date.month
    elif year == start_date.year:
        return start_date.month, 12
    elif year == end_date.year:
        return 1, end_date.month
    else:
        return 1, 12


def get_period_dates(
    year: int, month: int, start_date_src: date, end_date_src: date
) -> Tuple[datetime, datetime]:
    if year == start_date_src.year and month == start_date_src.month:
        start_dt = datetime(year, month, start_date_src.day)
    else:
        start_dt = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    month_end = datetime(year, month, last_day, 23, 59, 59)
    end_dt = min(
        month_end,
        datetime(end_date_src.year, end_date_src.month, end_date_src.day, 23, 59, 59),
    )

    return start_dt, end_dt

async def collect_uni_stats(
    webname: str, start_date: date, end_date: date, socials: List[str], app: Client
) -> dict:
    if not webname:
        return {"result": "error", "message": "Webname is required."}
    data = list()
    # async with Client(tg_session_name, api_id=tg_api_id, api_hash=tg_api_hash, no_updates=True, in_memory=True) as app:
    uni_info = get_socials(webname)
    if not uni_info:
        return {
            "result": "error",
            "message": "University not found or no social media data available.",
        }
    try:
        uni_short_name = uni_info["shortName"]
        uni_id = uni_info["id"]
        uni_vk = uni_info["vk"]
        uni_tg = uni_info["tg"]
        uni_rutube = uni_info["rutube"]
    except KeyError:
        print(f"Invalid university data format for {webname}.")
        return {
            "result": "error",
            "message": "Invalid university data format.",
        }
    rutube_stats_dict = (
        rutube_posts_and_views_parser(
            datetime(start_date.year, start_date.month, start_date.day, 23, 59, 59),
            uni_rutube
        )
        if uni_rutube and "rutube" in socials
        else {}
    )
    for year in range(start_date.year, end_date.year + 1):
        mrate = get_rating_data(uni_id, year)
        month_start, month_end = get_month_range(start_date, end_date, year)
        for month in range(month_start, month_end + 1):
            start_dt, end_dt = get_period_dates(year, month, start_date, end_date)
            rutube_posts, rutube_views = (
                (rutube_stats_dict.get(start_dt.strftime("%m.%Y"), (0, 0)))
                if "rutube" in socials
                else (0, 0)
            )
            posts_tg, views_tg, reacts_tg, forwards_tg = (
                await tg_ultimate_parser(uni_tg, start_dt, end_dt, app)
                if uni_tg and "tg" in socials
                else (0, 0, 0, 0)
            )
            comments_tg = (
                await tg_comments_counter(uni_tg, start_dt, end_dt, app)
                if uni_tg and "tg" in socials
                else 0
            )
            (
                mrate_cons,
                mrate_socials,
                mrate_vk,
                mrate_tg,
                mrate_rutube,
                mrate_site,
                mrate_smi,
            ) = mrate[month - 1]
            posts_vk, views_vk, reacts_vk, reposts_vk, comments_vk = (
                (vk_ultimate_parser(uni_vk, start_dt, end_dt, vk_access_token))
                if uni_vk and "vk" in socials
                else (0, 0, 0, 0, 0)
            )
            data.append(
                {
                    "month": months_rus.get(month),
                    "mrating": mrate_cons,
                    "mrating_socials": mrate_socials,
                    "mrating_vk": mrate_vk,
                    "mrating_tg": mrate_tg,
                    "mrating_rutube": mrate_rutube,
                    "mrating_site": mrate_site,
                    "mrating_smi": mrate_smi,
                    "posts_vk": posts_vk,
                    "views_vk": views_vk,
                    "reacts_vk": reacts_vk,
                    "reposts_vk": reposts_vk,
                    "comments_vk": comments_vk,
                    "posts_tg": posts_tg,
                    "views_tg": views_tg,
                    "reacts_tg": reacts_tg,
                    "forwards_tg": forwards_tg,
                    "comments_tg": comments_tg,
                    "posts_rutube": rutube_posts,
                    "views_rutube": rutube_views,
                }
            )
    return {"university": uni_short_name, "data": data}
