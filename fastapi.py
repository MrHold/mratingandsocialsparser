from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from .mratingparser import get_socials, get_unis
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from .rutubeparser import rutube_posts_and_views_parser
from .mratingparser import get_rating_data
from .ultimatetgparser import tg_ultimate_parser
from .commentstgcounter import tg_comments_counter
from .vkultimateparser import vk_ultimate_parser

import calendar
import openpyxl
import tempfile
from pyrogram import Client
import os
from dotenv import load_dotenv

load_dotenv()

vk_access_token = os.environ.get("VK_ACCESS_TOKEN")
tg_api_id = os.environ.get("TG_API_ID")
tg_api_hash = os.environ.get("TG_API_HASH")
tg_session_name = os.environ.get("TG_SESSION_NAME")

async def main(
    vk_group_id,
    rutube_channel_id,
    tg_channel_username,
    mrating_id,
    start_dt_src,
    end_dt_src,
):
    res = dict()
    async with Client(tg_session_name, api_id=tg_api_id, api_hash=tg_api_hash) as app:
        mrate = get_rating_data(mrating_id, 2025)
        rutube_posts_and_views = rutube_posts_and_views_parser(
            datetime(2025, 1, 1), rutube_channel_id
        ) if rutube_channel_id else {}
        for year in range(start_dt_src.year, end_dt_src.year + 1):
            month_start, month_end = 1, 12
            if year == start_dt_src.year == end_dt_src.year:
                month_end = end_dt_src.month
                month_start = start_dt_src.month
            elif year == start_dt_src.year:
                month_start = start_dt_src.month
                month_end = 12
            elif year == end_dt_src.year:
                month_start = 1
                month_end = end_dt_src.month
            else:
                month_start = 1
                month_end = 12

            for month in range(month_start, month_end + 1):
                if year == start_dt_src.year and month == start_dt_src.month:
                    start_dt = datetime(year, month, start_dt_src.day)
                else:
                    start_dt = datetime(year, month, 1)
                rutube_posts, rutube_views = 0, 0
                if rutube_posts_and_views.get(start_dt.strftime("%m.%Y"), 0):
                    rutube_posts, rutube_views = rutube_posts_and_views[
                        start_dt.strftime("%m.%Y")
                    ] if rutube_posts_and_views else (0, 0)
                end_dt = min(
                    datetime(
                        start_dt.year,
                        start_dt.month,
                        calendar.monthrange(start_dt.year, start_dt.month)[1],
                        23,
                        59,
                        59,
                    ),
                    end_dt_src,
                )
                posts_tg, views_tg, reacts_tg, forwards_tg = await tg_ultimate_parser(
                    tg_channel_username, start_dt, end_dt, app
                ) if tg_channel_username else (0, 0, 0, 0)
                comments_tg = await tg_comments_counter(
                    tg_channel_username, start_dt, end_dt, app
                ) if tg_channel_username else 0
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
                    vk_ultimate_parser(vk_group_id, start_dt, end_dt, vk_access_token)
                ) if vk_group_id else (0, 0, 0, 0, 0)
                res[month] = {
                    "М-рейтинг": mrate_cons,
                    "М-рейтинг СоцСети": mrate_socials,
                    "М-рейтинг ВК": mrate_vk,
                    "М-рейтинг ТГ": mrate_tg,
                    "М-рейтинг Рутуб": mrate_rutube,
                    "М-рейтинг Сайт": mrate_site,
                    "М-рейтинг СМИ": mrate_smi,
                    "Публикаций ВК": posts_vk,
                    "Просмотров ВК": views_vk,
                    "Реакций ВК": reacts_vk,
                    "Репостов ВК": reposts_vk,
                    "Комментариев ВК": comments_vk,
                    "Публикаций ТГ": posts_tg,
                    "Просмотров ТГ": views_tg,
                    "Реакций ТГ": reacts_tg,
                    "Репостов ТГ": forwards_tg,
                    "Комментариев ТГ": comments_tg,
                    "Публикаций Рутуб": rutube_posts,
                    "Просмотров Рутуб": rutube_views,
                }
    return res

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/get_unis_list")
def get_unis_list():
    return get_unis()

@app.get("/get_uni_socials/{webname}")
def get_uni_socials(webname: str):
    return get_socials(webname)

@app.get("/get_uni_stats/")
async def get_uni_stats(webname: str, start_date: Optional[str] = Query(None, format="YYYY-MM-DD"), end_date: Optional[str] = Query(None, format="YYYY-MM-DD")):
    m_id, tg, vk, rutube = get_socials(webname).values()
    start_dt = datetime(*list(map(int, start_date.split("-"))), 0, 0, 0)
    end_dt = datetime(*list(map(int, end_date.split("-"))), 23, 59, 59)
    return await main(vk, rutube, tg, m_id, start_dt, end_dt)

class StatsRequest(BaseModel):
    webname: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    platforms: List[str]  # ["vk", "tg", "rutube"]

@app.post("/generate_stats_table")
async def generate_stats_table(req: StatsRequest):
    m_id, tg, vk, rutube = get_socials(req.webname).values()

    start_dt = datetime.strptime(req.start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(req.end_date, "%Y-%m-%d")

    return await main(
        vk_group_id=vk if "vk" in req.platforms else None,
        rutube_channel_id=rutube if "rutube" in req.platforms else None,
        tg_channel_username=tg if "tg" in req.platforms else None,
        mrating_id=m_id,
        start_dt_src=start_dt,
        end_dt_src=end_dt,
    )

class XLSXRequest(BaseModel):
    webname: str
    start_date: str  # "YYYY-MM-DD"
    end_date: str    # "YYYY-MM-DD"
    platforms: List[str]

@app.post("/download_xlsx")
async def download_xlsx(req: XLSXRequest):
    m_id, tg, vk, rutube = get_socials(req.webname).values()

    start_dt = datetime.strptime(req.start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(req.end_date, "%Y-%m-%d")

    result = await main(
        vk_group_id=vk if "vk" in req.platforms else None,
        rutube_channel_id=rutube if "rutube" in req.platforms else None,
        tg_channel_username=tg if "tg" in req.platforms else None,
        mrating_id=m_id,
        start_dt_src=start_dt,
        end_dt_src=end_dt,
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Результаты"

    # Заголовки: первая колонка — месяц, дальше все ключи из одного месяца
    months = sorted(result.keys())
    if not months:
        raise Exception("Нет данных для выбранного диапазона.")

    # Получение метрик из первого месяца
    metrics = list(result[months[0]].keys())
    headers = ["Месяц"] + metrics
    ws.append(headers)

    # Добавление строк
    for month in months:
        row = [calendar.month_name[int(month)]]
        for metric in metrics:
            row.append(result[month].get(metric, ""))
        ws.append(row)

    # Сохранение во временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        wb.save(tmp.name)
        temp_path = tmp.name

    return FileResponse(
        path=temp_path,
        filename="университет_статистика.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )