import requests
from datetime import datetime
from pprint import pprint

rutube_channel_id = 23788073

def rutube_posts_and_views_parser(end_dt: datetime, rutube_channel_id: int) -> dict:
    if not rutube_channel_id:
        return {0, 0}
    res = dict()
    f = False
    for i in range(1, 200):
        if f:
            break
        response = requests.get(f"https://rutube.ru/api/video/person/{rutube_channel_id}/?page={i}")
        data = response.json()
        if data.get('detail', 0):
            break
        for j in data['results']:
            post_date = datetime.fromisoformat(j['publication_ts'])
            if post_date < end_dt:
                f = True
                break
            post_views = j['hits'] if j['hits'] else 0
            if not res.get(post_date.strftime("%m.%Y"), 0):
                res[post_date.strftime("%m.%Y")] = [1, post_views]
            else:
                res[post_date.strftime("%m.%Y")][0] += 1
                res[post_date.strftime("%m.%Y")][1] += post_views
    return res

if __name__ == "__main__":
    res = rutube_posts_and_views_parser(datetime(2025, 5, 1, 0, 0, 0), rutube_channel_id)
    pprint(res)