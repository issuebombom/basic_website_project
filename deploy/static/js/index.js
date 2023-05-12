$(document).ready(function () {
  movieListing();
});

function movieListing() {
  $('#cards-box').empty()

  fetch('/movies').then((res) => res.json()).then((data) => {
    let rows = data['movies']

    rows.forEach((row, idx) => {
      let { movie_id, title, grade, content, poster_url, open_date, reserve_ratio } = row
      let star_repeat = "⭐".repeat(grade)

      $('#title').append(`<option value=${movie_id}>${idx + 1}. ${title}</option>`)
      let temp_html = `<div class="col">
                        <div class="card h-100">
                          <img src=${poster_url} class="card-img-top" onError="this.src='../static/images/no_img.png'">
                          <div class="card-body">
                            <a href=/reviews?movieId=${movie_id}&page=1&limit=20 target="_blank" class="card-title">${idx + 1}. ${title}</a>
                            <p class="card-text">${star_repeat} (${grade})</p>
                            <p class="card-text">${content}</p>
                            <p class="card-text" style="margin-bottom: 0px;">개봉일: ${open_date}</p>
                            <p class="card-text">예매율: ${reserve_ratio}</p>
                          </div>
                        </div>
                      </div>`
      $('#cards-box').append(temp_html)
    })
  })
};

function posting() {
  let formData = new FormData();
  formData.append("movieId", inputChecker($("#title-label").text(), $("#title").val()));
  formData.append("grade", inputChecker($("#grade-label").text(), $("#grade").val()));
  formData.append("nickname", inputChecker($("#nickname-label").text(), $("#nickname").val()));
  formData.append("comment", inputChecker($("#comment-label").text(), $("#comment").val()));

  fetch('/reviews', { method: "POST", body: formData }).then((res) => res.json()).then((data) => {
    alert(data['msg']);
    window.location.reload();
  })
};

function inputChecker(target, content) {
  const trimString = content.trim()
  if (trimString.length === 0) {
    alert(`${target}을(를) 입력하세요.`);
    throw new Error(`${target}을(를) 입력하지 않았습니다.`);
  } else {
    return content
  };
};

function open_box() {
  $('#post-box').show()
};
function close_box() {
  $('#post-box').hide()
};
