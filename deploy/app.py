from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient, DESCENDING
from datetime import datetime

client = MongoClient(
    "mongodb+srv://issuebombom:test@testcluster.bcnelb9.mongodb.net/?retryWrites=true&w=majority"
)
db = client.dbspartaproject01

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/reviews")
def reviews():
    return render_template("reviews.html")


@app.route("/movies")
def get_movie():
    movies = list(db.movies.find({}, {"_id": False}))
    return jsonify({"movies": movies})


@app.route("/reviews", methods=["POST"])
def post_review():
    movie_id = request.form["movieId"]
    grade = request.form["grade"]
    nickname = request.form["nickname"]
    comment = request.form["comment"]

    # 현재 시각
    now = datetime.now()
    now = datetime.strftime(now, "%Y-%m-%d %H:%M:%S")

    review = {
        "movie_id": movie_id,
        "grade": grade,
        "nick_name": nickname,
        "comment": comment,
        "upload_time": now,
    }

    db.reviews.insert_one(review)

    return jsonify({"msg": "등록을 완료했습니다."})


@app.route("/apis/reviews", methods=["GET"])
def get_review():
    movie_id = request.args.get("movieId")  # 만약 없으면 None
    page = int(request.args.get("page"))
    limit = int(request.args.get("limit"))
    limit = limit if limit <= 50 else 50

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


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
