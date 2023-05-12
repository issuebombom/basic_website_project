# Javascript 와 Flask를 활용한 미니 웹개발 프로젝트 정리

![Alt text](deploy/static/images/result.png)

## 프로젝트 목표
최신 영화 목록에 대해 별점과 코멘트를 등록할 수 있고, 각 영화마다 현재까지 달린 코멘트를 확인할 수 있다.

## 구현 내용
### 영화 정보 스크래핑
`DAUM 영화 사이트에서 현재 애매순위 TOP 20에 해당하는 영화의 메타정보를 수집한다.`

#### 고민했던 부분  
1. 메인페이지에서 영화 제목을 클릭하면 지금까지 축적된 해당 영화의 코멘트를 보여주도록 API를 구현하는 과정에서 각 영화의 고유 ID 정보가 필요했다.  
처음에는 MongoDB에서 자동으로 생성해주는 ObjectId 타입의 '_id'컬럼을 사용하려 했으나 해당 타입이 string이 아닌 관계로 jsonString으로 프론트에 전달하기 위해서는 String 타입으로 변경해주는 작업이 추가적으로 필요했다.  
하지만 MongoDB에서 데이터를 find할 때 ObjectId를 사전에 String타입으로 가져오는 방법이 없어 iteration을 통해 따로 ObjectId 타입을 변경해주는 추가 작업이 필요했는데 이 과정을 제외하고 싶었다. 무엇보다 데이터가 늘어날수록 계산 비용을 증가시키는 요인이 될 것이기 때문이다.  

```python
# 최초 objectId 타입을 String 타입으로 변환하는 코드를 작성했다.
result = db.collection.find({}) # dict가 담긴 list 형태로 출력

# _id 값을 문자열로 변환하여 JSON으로 전달
for obj in result:
  obj['_id'] = str(obj['_id'])

json_result = json.dumps(result)
```

이는 반대로 mongoDB의 '_id' 조회 시 다시 ObjectId 타입으로 돌려놓는 작업을 동반한다.
```python
from bson.objectid import ObjectId

doc = db.collection.find_one({"_id": ObjectId("614c231c7e1bf330ee9a3f3a")})
```

위 과정을 해소하기 위해 DAUM 영화 사이트에서 규정한 영화의 고유 ID를 스크랩 과정에서 가져와서 대신 primary key로 사용하기로 했다.  
해당 데이터는 유일성이 보장이 되기 때문에 movie_id로서 사용하기에 적합했기 때문이다.  
추가적으로 DAUM 영화 사이트 html에는 각 영화의 id를 직접적으로 포함한 태그가 없어 href 요소에서 id 부분을 추출하는 방식으로 데이터를 획득했다.
```python
soup = BeautifulSoup(res.text, "html.parser")
movie_infos = []
for tag in soup.select(".item_poster"):
    movie_id = re.sub("[^0-9]", "", tag.select_one(".tit_item .link_txt")["href"])

    return movie_infos
```

2. 영화 데이터와 해당 영화의 댓글 데이터를 함께 수집하고 싶었다.
> DAUM에서 쓰는 영화 고유 id와 각 영화의 코멘트 게시판 id가 달랐지만 이를 매칭할 수 있는 API가 존재했다.
아래 request가 이에 해당하는데 계속 status_code 401이 출력되어 json을 받을 수 없었다.  
결국 header에서 authorization을 기입하고 나서 200이 출력되었다.
특정 GET 요청에 있어 authorization도 요구될 수 있다는 점을 알게되었다.  
하지만 authorization의 value가 정기적으로 바뀌므로 이에 따른 코드 수정이 필요하다.
```python
def get_post_id(movie_id):
    """movie_id를 입력하면 해당 영화의 코멘트 post_id를 출력

    Args:
        movie_id (int): movie_id

    Returns:
        int: post_id
    """

    url = f"https://comment.daum.net/apis/v1/ui/single/main/@{movie_id}"
    params = {"version": "v3.23.0"}
    headers = {
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.....",
        "referer": "https://movie.daum.net/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    }

    res = requests.get(url, params=params, headers=headers)
    data = json.loads(res.text)
    post_id = data["post"]["id"]

    return post_id
```

### MongoDB 연결 이슈
`IP Address가 변경될 경우 Atlas에 접속하여 Current IP Address를 추가해줘야 정상적으로 작동한다는 것을 알았다.  
개인적으로 가정 와이파이를 사용하다가 휴대폰 테더링으로 변경했더니 `ServerSelectionTimeoutError`가 발생했다.  
이를 통해 MongoDB에서 사전에 등록된 IP Address에게 접속 권한을 허용한다는 것을 알 수 있었다.

### html 전환
`메인페이지에 나열된 특정 영화 제목 중 하나를 클릭하면 reviews.html 페이지로 넘어가되 reviews 페이지의 골격은 유지하면서 movie_id에 따라 콘텐츠가 다르게 적용되도록 구현한다.`

#### 고민했던 부분
20개의 영화를 대상으로 각각 href를 적용하고 싶지는 않았다.  
그래서 a 태그의 href를 활용하여 클릭 시 reviews.html로 넘기는 과정에서 movie_id를 전달하고, reviews.html에서 받는 방법을 몰랐었는데 아래와 같이 해결할 수 있었다.  

> 먼저 다른 html로 이동하기 위해서는 랜더링 설정이 필요하다. flask 기준에서는 아래와 같이 작성한다.
```python
@app.route("/reviews")
def reviews_page():
    return render_template("reviews.html")
```
> 이동하고자 하는 reviews.html파일의 쿼리로 movie_id 데이터를 전달할 수 있다.  
```html
<script>
  let temp_html = `<a href=/reviews?movieId=${movie_id} target="_blank" class="card-title">영화 제목</a>`
  $('#cards-box').append(temp_html)
</script>
```
> reviews.html에서는 아래와 같이 `URLSearchParams` 메소드를 통해 쿼리 데이터를 받아 변수로 저장할 수 있다.
```html
<script>
  const urlParams = new URLSearchParams(window.location.search);
  const movieId = urlParams.get('movieId');
</script>
```

추가적인 시도 방법은 아래와 같다.
```python
@app.route("/reviews/<movie_id>", methods=["GET"])
def get_review(movie_id):
    # MongoDB에서 리뷰 데이터 가져오기
    movie = list(db.movies.find({"movie_id": movie_id}, {"_id": False}))
    comments = list(
        db.reviews.find({"movie_id": movie_id}, {"_id": False}).sort(
            "upload_time", DESCENDING
        )
    )
    reviews = {"movie": movie, "comments": comments}
    return render_template("reviews.html", reviews=reviews)
```
```javascript
const reviews = JSON.parse('{{ reviews | tojson}}');
```
영화 제목 태그의 href를 `/reviews/${movie_id}`로 설정하여 fetch함수 없이 바로 백엔드로 보내도록 시도해보았다.  
하지만 render_template 함수에서 html 랜더링과 함께 전달할 수 있는 데이터 길이에 한계가 있는 것으로 보였다.  
프론트에서 전달받은 jsonString의 길이가 비교적 짧은 경우에는 프론트에 잘 출력이 되었지만 긴 경우 JSON.parse 과정에서 오류가 발생하였다.  
이는 jsonString이 도중에 잘려나가는 바람에 온전한 json 형태가 아니게 되어서인 것으로 추측된다.  

### 레이아웃
`영화 포스터에서 영화 제목과 내용이 일정 길이를 넘어서면 "..."으로 처리되도록 하여 노출을 제한하고 싶었다.`

#### 고민했던 부분
1. 글자 길이에 따라 display가 flexable하게 변동되어 레이아웃이 엉망이 되었다. 이를 해결하고자 아래 방법을 채택했다.
> 영화 제목의 경우 줄바꿈 없이 생략되도록 아래와 같이 적용할 수 있다.  
width설정을 통해 길이 제한, `ellipsis`는 생략 기호 사요으 `nowrap`으로 줄바꿈을 방지한다.
```css
/* a 태그 */
.card-title { 
  display: block;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* p 태그 */
.my-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 150px;
}

```
> 4줄 이상 overflow 시 생략하는 방법은 아래와 같다.
```css
/* p 태그 */
.card-text {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

2. 리뷰 입력란에서 옵션 미선택 또는 문자를 입력하지 않을 경우에 대한 예외처리를 하고 싶었다.
> 빈칸이 입력될 경우 경고창이 뜨고 코드 수행을 중단하도록 했다.  
함수의 target 메서드는 입력되지 않은 레이블의 텍스트를 받아 알림 문구가 유동적이게 하였다.  
띄어쓰기로만 입력된 경우에도 입력되지 않은 것으로 간주하기 위해 trim 메서드를 적용했다.  
```html
<script>
  function inputChecker(target, content) {
    const trimString = content.trim()
    if (trimString.length === 0) {
      alert(`${target}을(를) 입력하세요.`)
      throw new Error(`${target}을(를) 입력하지 않았습니다.`)
    } else {
      return content
    }
  };
</script>
```

리뷰 기록의 POST 요청을 위한 value 획득 과정에서 각 value의 label도 함께 inputChecker 함수로 전달했다.
```html
<script>
  let formData = new FormData();
  formData.append("movieId", inputChecker($("#title-label").text(), $("#title").val()));
  formData.append("grade", inputChecker($("#grade-label").text(), $("#grade").val()));
  formData.append("nickname", inputChecker($("#nickname-label").text(), $("#nickname").val()));
  formData.append("comment", inputChecker($("#comment-label").text(), $("#comment").val()));
</script>
```

### 페이지네이션 구현
`reviews 페이지에서 한 페이지 당 20개의 코멘트만 노출되도록 하는 페이지 네이션 구현`

#### 고민했던 부분
시간 관계 상 previous와 next 버튼 구현을 하지 못했다. 당장 어떤 식으로 구현이 되어야 하는지 아이디어가 떠오르지 못했다.

#### 과정
1. href를 통해 페이지네이션에 필요한 정보들을 담아 전달했다.
    ```html
    <script>
      `<a href=/reviews?movieId=${movie_id}&page=1&limit=20 target="_blank" class="card-title">${idx + 1}. ${title}</a>`
    </script>
    ```
2. reviews.html에 접속하면 가장 먼저 쿼리값을 변수에 담는다.
    ```javascript
    const urlParams = new URLSearchParams(window.location.search);
    const movieId = urlParams.get('movieId');
    const page = Number(urlParams.get('page'));
    const limit = urlParams.get('limit');
    ```

3. 백엔드에서는 MongoDB에서 필요한 정보를 가져온다. 이 때 page와 limit 변수를 활용하여 페이지별 보여줘야 할 코멘트가 순차적으로 달라질수 있도록 한다. 특히 한 페이지에서 볼 수 있는 코멘트의 최대량이 50을 넘지 않도록 한다.
    ```python
    @app.route("/apis/reviews", methods=["GET"])
    def get_review():
        movie_id = request.args.get("movieId")
        page = int(request.args.get("page"))
        limit = int(request.args.get("limit"))
        limit = limit if limit <= 50 else 50 # 한 페이지 보기 제한 최대 50개

        # MongoDB에서 리뷰 데이터 가져오기
        movie = list(db.movies.find({"movie_id": movie_id}, {"_id": False}))
        comments = list(
            db.reviews.find({"movie_id": movie_id}, {"_id": False})
            .skip((page - 1) * limit)
            .limit(limit)
            .sort("upload_time", DESCENDING)
        )
        count = db.reviews.count_documents({"movie_id": movie_id})

        return jsonify({"movie": movie, "comments": comments, "count": count})
    ```
4. MongoDB에서 필터링을 통해 영화에 담긴 코멘트의 총 개수를 `count` 변수에 담아냈고, 한 페이지에 보여줄 카드의 개수를 `limit` 변수에 담았다. 특히 현재 내가 머물고 있는 페이지에 대해서는 다른 태그를 추가해서 디자인적으로 구분한다.
    ```javascript
    let last_page = Math.floor(count / limit) + 1;
    let pagination_html;
    for (let i = 1; i <= last_page; i++) {
      let url = `/reviews?movieId=${movieId}&page=${i}&limit=${limit}`
      if (i === page) {
        pagination_html = `<li class="page-item active" aria-current="page">
                            <span class="page-link">${i}</span>
                          </li>`
      } else {
        pagination_html = `<li class="page-item"><a class="page-link" href=${url}>${i}</a></li>`
      };

      $('#pagination').append(pagination_html)
    }
    ```

