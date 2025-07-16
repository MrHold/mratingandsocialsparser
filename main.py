from fastapi import FastAPI, Query, APIRouter
from fastapi.responses import FileResponse
from datetime import datetime, date
from typing import Optional, Tuple, List
import calendar
import openpyxl
import tempfile
from pyrogram import Client
import os
from dotenv import load_dotenv

from .services.parsers.rutubeparser import rutube_posts_and_views_parser
from .services.parsers.mratingparser import get_rating_data, get_socials, get_unis, months_rus
from .services.parsers.ultimatetgparser import tg_ultimate_parser
from .services.parsers.commentstgcounter import tg_comments_counter
from .services.parsers.vkultimateparser import vk_ultimate_parser
from .models.schemas import AnalyzeRequest


load_dotenv()

vk_access_token = os.environ.get("VK_ACCESS_TOKEN")
tg_api_id = os.environ.get("TG_API_ID")
tg_api_hash = os.environ.get("TG_API_HASH")
tg_session_name = os.environ.get("TG_SESSION_NAME")

def get_month_range(start_date: date, end_date: date, year: int) -> Tuple[int, int]:
    if year == start_date.year == end_date.year:
        return start_date.month, end_date.month
    elif year == start_date.year:
        return start_date.month, 12
    elif year == end_date.year:
        return 1, end_date.month
    else:
        return 1, 12    

def get_period_dates(year: int, month: int, start_date_src: date, end_date_src: date) -> Tuple[datetime, datetime]:
    if year == start_date_src.year and month == start_date_src.month:
        start_dt = datetime(year, month, start_date_src.day)
    else:
        start_dt = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    month_end = datetime(year, month, last_day, 23, 59, 59)
    end_dt = min(month_end, datetime(end_date_src.year, end_date_src.month, end_date_src.day, 23, 59, 59))

    return start_dt, end_dt

async def collect_uni_stats(
    webname: str,
    start_date: date,
    end_date: date,
    socials: List[str]
) -> dict:
    if not webname:
        return {"result": "error", "message": "Webname is required."}
    data = list()
    async with Client(tg_session_name, api_id=tg_api_id, api_hash=tg_api_hash) as app:
        uni_info = get_socials(webname)
        if not uni_info:
            return {"result": "error", "message": "University not found or no social media data available."}
        uni_short_name = uni_info["shortName"]
        uni_id = uni_info["id"]
        uni_vk = uni_info["vk"]
        uni_tg = uni_info["tg"]
        uni_rutube = uni_info["rutube"]
        rutube_stats_dict = rutube_posts_and_views_parser(datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59), uni_rutube) if uni_rutube and "rutube" in socials else {}
        for year in range(start_date.year, end_date.year + 1):
            mrate = get_rating_data(uni_id, year)
            month_start, month_end = get_month_range(start_date, end_date, year)
            for month in range(month_start, month_end + 1):
                
                start_dt, end_dt = get_period_dates(
                    year, month, start_date, end_date)
                rutube_posts, rutube_views = (
                    rutube_stats_dict.get(start_dt.strftime("%m.%Y"), (0, 0))
                ) if "rutube" in socials else (0, 0)
                posts_tg, views_tg, reacts_tg, forwards_tg = (
                    await tg_ultimate_parser(uni_tg, start_dt, end_dt, app)
                    if uni_tg and "tg" in socials
                    else (0, 0, 0, 0)
                )
                comments_tg = (
                    await tg_comments_counter(
                        uni_tg, start_dt, end_dt, app
                    )
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
                data.append({
                    "month": months_rus.get(month),
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
                })
    return {"university": uni_short_name, "data": data}


app = FastAPI()
router = APIRouter()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@router.post("/analyze")
async def analyze_endpoint(data: AnalyzeRequest):
    universities = [x.webname for x in data.universities]
    results = {}
    for webname in universities:
        results[webname] = await collect_uni_stats(webname, data.start_date, data.end_date, data.socials)

    return results

@router.post("/export")
async def export_endpoint(data: AnalyzeRequest):
    return {"result": "Excel"}

@app.get("/universities")
async def universities():
    return get_unis()


# @app.get("/get_uni_socials/{webname}")
# async def get_uni_socials(webname: str):
#     return get_socials(webname)


# @app.get("/get_uni_stats/")
# async def get_uni_stats(
#     webname: str,
#     start_date: Optional[str] = Query(None, format="YYYY-MM-DD"),
#     end_date: Optional[str] = Query(None, format="YYYY-MM-DD"),
# ):
#     m_id, tg, vk, rutube = get_socials(webname).values()
#     start_dt = datetime(*list(map(int, start_date.split("-"))), 0, 0, 0)
#     end_dt = datetime(*list(map(int, end_date.split("-"))), 23, 59, 59)
#     return await main(vk, rutube, tg, m_id, start_dt, end_dt)


app.include_router(router)


# class StatsRequest(BaseModel):
#     webname: str
#     start_date: str  # YYYY-MM-DD
#     end_date: str    # YYYY-MM-DD
#     platforms: List[str]  # ["vk", "tg", "rutube"]

# @app.post("/generate_stats_table")
# async def generate_stats_table(req: StatsRequest):
#     m_id, tg, vk, rutube = get_socials(req.webname).values()

#     start_dt = datetime.strptime(req.start_date, "%Y-%m-%d")
#     end_dt = datetime.strptime(req.end_date, "%Y-%m-%d")

#     return await main(
#         vk_group_id=vk if "vk" in req.platforms else None,
#         rutube_channel_id=rutube if "rutube" in req.platforms else None,
#         tg_channel_username=tg if "tg" in req.platforms else None,
#         mrating_id=m_id,
#         start_dt_src=start_dt,
#         end_dt_src=end_dt,
#     )

# class XLSXRequest(BaseModel):
#     webname: str
#     start_date: str  # "YYYY-MM-DD"
#     end_date: str    # "YYYY-MM-DD"
#     platforms: List[str]

# @app.post("/download_xlsx")
# async def download_xlsx(req: XLSXRequest):
#     m_id, tg, vk, rutube = get_socials(req.webname).values()

#     start_dt = datetime.strptime(req.start_date, "%Y-%m-%d")
#     end_dt = datetime.strptime(req.end_date, "%Y-%m-%d")

#     result = await main(
#         vk_group_id=vk if "vk" in req.platforms else None,
#         rutube_channel_id=rutube if "rutube" in req.platforms else None,
#         tg_channel_username=tg if "tg" in req.platforms else None,
#         mrating_id=m_id,
#         start_dt_src=start_dt,
#         end_dt_src=end_dt,
#     )

#     wb = openpyxl.Workbook()
#     ws = wb.active
#     ws.title = "Результаты"

#     # Заголовки: первая колонка — месяц, дальше все ключи из одного месяца
#     months = sorted(result.keys())
#     if not months:
#         raise Exception("Нет данных для выбранного диапазона.")

#     # Получение метрик из первого месяца
#     metrics = list(result[months[0]].keys())
#     headers = ["Месяц"] + metrics
#     ws.append(headers)

#     # Добавление строк
#     for month in months:
#         row = [calendar.month_name[int(month)]]
#         for metric in metrics:
#             row.append(result[month].get(metric, ""))
#         ws.append(row)

#     # Сохранение во временный файл
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
#         wb.save(tmp.name)
#         temp_path = tmp.name

#     return FileResponse(
#         path=temp_path,
#         filename="университет_статистика.xlsx",
#         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
