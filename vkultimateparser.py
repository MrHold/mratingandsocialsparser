import vk_api
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def vk_ultimate_parser(vk_group_id, start_dt, end_dt, vk_access_token):
    vk_session = vk_api.VkApi(token=vk_access_token) # авторизация
    vk = vk_session.get_api()
    comments = 0
    likes_count = 0
    count = 0
    reposts = 0
    views = 0
    start_date = int(start_dt.timestamp())  # начало года
    end_date = int(end_dt.timestamp())  # конец года

    offset = 0

    while True:
        response = vk.wall.get(
            owner_id=vk_group_id,  # ID группы (отрицательное число для групп)
            count=100,          # Максимум 100 постов за раз
            offset=offset,
            filter='owner'      # Только посты от имени группы
        )
        
        posts = response['items']
        for post in posts:
            post_date = post['date']
            if post.get('is_pinned', 0) == 1:
                continue
            if start_date <= post_date <= end_date:
                count += 1
                comments += post['comments']['count']
                likes_count += post['likes']['count']
                reposts += post['reposts']['count']
                views += post.get('views', {}).get('count', 0)
            if post_date < start_date:
                # Если наткнулись на пост старше года, прерываем цикл
                return count, views, likes_count, reposts, comments
        
        # Если достигли конца списка постов
        if len(posts) < 100:
            break

        offset += 100  # Переход к следующему блоку постов

    return count, views, likes_count, reposts, comments

if __name__ == "__main__":
    GROUP_ID = -202438557
    ACCESS_TOKEN = os.environ.get("VK_ACCESS_TOKEN")

    start_dt = datetime(2025, 4, 18)
    end_dt = datetime(2025, 4, 30)
    likes_count = vk_ultimate_parser(GROUP_ID, start_dt, end_dt, ACCESS_TOKEN)
