import requests
import json

rutypes = {
    "consolidated": "Сводный",
    "social": "Социальные сети",
    "social_vkontakte": "ВКонтакте",
    "social_telegram": "Telegram",
    # "social_odnoklassniki": "Одноклассники",
    "social_rutube": "RUTUBE",
    "site": "Сайт",
    "smi": "СМИ"
}

year = "2024"

months_rus = {
    1: "Январь", 2: "Февраль", 3: "Март",
    4: "Апрель", 5: "Май", 6: "Июнь",
    7: "Июль", 8: "Август", 9: "Сентябрь",
    10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

mrate_months = ["Янв.", "Февр.", "Март", "Апр.", "Май", "Июнь", "Июль",
                 "Авг.", "Сент.", "Окт.", "Нояб.", "Дек."]

url_template = "https://xn----ftbfmepluu.xn--p1ai/api/universities/{id}/chart?type={type}&year={year}"

def get_unis():
    url = "https://xn----ftbfmepluu.xn--p1ai/api/universities/rating?type=consolidated&query="
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        elements = data.get("elements", [])
        res = {i["shortName"]: {"id": i["id"], "webname": i["webname"]} for i in elements}
        return {k: v for k, v in sorted(res.items())}
    except requests.RequestException as e:
        print(f"Ошибка запроса: {e}")
    except json.JSONDecodeError as e:
        print(f"Ошибка обработки JSON: {e}")

def get_socials(webname: str) -> list:
    url = "https://xn----ftbfmepluu.xn--p1ai/api/universities/" + webname
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        res = {
            "id": 0,
            "tg": "",
            "vk": "",
            "rutube": ""
        }
        res["id"] = int(data["university"]["id"])
        for i in data["university"]["socialNetworks"]:
            if i["type"] == "telegram":
                res["tg"] = i["url"].replace("https://t.me/", "").replace("http://t.me/", "").rstrip("/")
            if i["type"] == "vkontakte":
                res["vk"] = i["url"].replace("https://vk.com/", "").replace("http://vk.com/", "").rstrip("/")
            if i["type"] == "rutube":
                res["rutube"] = i["url"].replace("https://rutube.ru/channel/", "").replace("http://rutube.ru/channel/", "").rstrip("/")
        return res
    except requests.RequestException as e:
            return {"result": "error"}
            print(f"Ошибка запроса: {e}")
    except json.JSONDecodeError as e:
        print(f"Ошибка обработки JSON: {e}")

def get_rating_data(id, year):
    res = []
    for type in rutypes.keys():
        url = url_template.format(id=id, type=type, year=year)
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            elements = data.get("elements", [])
            if elements:
                type = []
                for month in mrate_months:
                    found = False
                    for i in elements:
                        if i.get('name', 0) == month:
                            found = True
                            type.append(i.get('position', 0))
                    if not found:
                        type.append(0)
                res.append(type) 
        except requests.RequestException as e:
            print(f"Ошибка запроса: {e}")
            return {"result": "error"}
        except json.JSONDecodeError as e:
            print(f"Ошибка обработки JSON: {e}")
    res = [list(row) for row in zip(*res)]
    return res



if __name__ == "__main__":
    id = 45
    print(get_socials("rudn"))
    print(get_rating_data(id, 2025))