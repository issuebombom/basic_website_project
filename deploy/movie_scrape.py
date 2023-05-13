import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import json
import re

# mongoDB client 정보
client = MongoClient(
    "mongodb+srv://<projectname>:<username>@testcluster.bcnelb9.mongodb.net/?retryWrites=true&w=majority"
)
db = client.dbspartaproject01
AUTH = "Bearer ..."


def get_post_id(movie_id, auth):
    """movie_id를 입력하면 해당 영화의 코멘트 post_id를 출력

    Args:
        movie_id (int): movie_id

    Returns:
        int: post_id
    """

    url = f"https://comment.daum.net/apis/v1/ui/single/main/@{movie_id}"
    params = {"version": "v3.24.0"}
    headers = {
        # auth값은 매일 변경됨
        "authorization": auth,
        "referer": "https://movie.daum.net/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    }

    res = requests.get(url, params=params, headers=headers)

    try:
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Request failed with status code {e.response.status_code}")

    data = json.loads(res.text)
    post_id = data["post"]["id"]

    return post_id


def get_comments(movie_id, auth):
    """코멘트 post id를 입력하면 코멘트 데이터를 수집

    Args:
        movie_id (int): movie_id

    Returns:
        list: 코멘트 데이터
    """

    post_id = get_post_id(movie_id, auth)
    offset = 0
    comments = []
    while True:
        url = f"https://comment.daum.net/apis/v1/posts/{post_id}/comments"
        params = {
            "parentId": 0,
            "offset": offset,
            "limit": 100,  # DAUM에서 한 번에 최대 100개까지 조회 가능하도록 설정됨
            "sort": "LATEST",
            "isInitial": "true",
            "hasNext": "true",
        }
        headers = {
            "referer": "https://movie.daum.net/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        }

        res = requests.get(url, params=params, headers=headers)
        data = json.loads(res.text)

        if len(data) == 0:
            break

        temp_comments = []
        for obj in data:
            comment = {
                "movie_id": movie_id,
                "grade": obj["rating"],
                "comment": obj["content"],
                "upload_time": re.sub("T", " ", obj["createdAt"])[:-5],
                "like_count": obj["likeCount"],
                "dislike_count": obj["dislikeCount"],
                "nick_name": obj["user"]["displayName"],
            }
            temp_comments.append(comment)
        offset += 100
        comments.extend(temp_comments)
    return comments


def get_movie_contents(comments=None):
    """DAUM Top 20 예매 순위 영화 데이터 스크랩

    Args:
        comments (bool): 각 영화의 코멘트 수집 여부. Defaults to None.

    Returns:
        list: dictionary 타입의 영화정보가 담긴 list
    """

    url = "https://movie.daum.net/ranking/reservation"

    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    movies_data = []
    comments_data = []
    for tag in soup.select(".item_poster"):
        rank = tag.select_one(".rank_num").get_text()
        title = tag.select_one(".tit_item .link_txt").get_text()
        movie_id = re.sub("[^0-9]", "", tag.select_one(".tit_item .link_txt")["href"])
        content = tag.select_one(".link_story").get_text().strip()
        grade = tag.select_one(".info_txt .txt_grade").get_text()
        reserve_ratio = tag.select_one(".info_txt .txt_num").get_text()
        open_date = tag.select_one(".txt_info .txt_num").get_text()
        if tag.find("img"):
            poster_url = tag.select_one(".poster_movie img")["src"]
        else:
            poster_url = None

        if comments:
            comments = get_comments(movie_id, AUTH)
            comments_data.extend(comments)

        movie = {
            "movie_id": movie_id,
            "rank": rank,
            "title": title,
            "content": content,
            "grade": grade,
            "reserve_ratio": reserve_ratio,
            "open_date": open_date,
            "poster_url": poster_url,
        }

        movies_data.append(movie)

    return movies_data, comments_data


def run():
    # 기존 데이터를 최신 데이터로 대체한다.
    movies, comments = get_movie_contents(comments=True)
    db.movies.drop()
    db.reviews.drop()
    db.movies.insert_many(movies)
    db.reviews.insert_many(comments)


if __name__ == "__main__":
    run()
