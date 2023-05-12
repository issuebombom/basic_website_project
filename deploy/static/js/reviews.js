const urlParams = new URLSearchParams(window.location.search);
const movieId = urlParams.get('movieId');
const page = Number(urlParams.get('page'));
const limit = urlParams.get('limit');
$(document).ready(function () {
  reviewListing();
});

function reviewListing() {
  fetch(`/apis/reviews?movieId=${movieId}&page=${page}&limit=${limit}`)
    .then((res) => res.json())
    .then((data) => {
      let { title, grade, content, poster_url } = data['movie'][0]
      let comments = data['comments']
      let count = data['count']

      $('#title').text(title);
      $('.avg-star').text(`평점: ${grade} (${count}명)`);
      $('.content').text(content);
      $('#comment-list').empty()
      
      if (comments.length === 0) {
        $('#comment-list').append(`<p style="text-align: center; font-size: 20px;">아직 댓글이 없어요...</p>`)
      } else {
        comments.forEach((row) => {
          let { nick_name, grade, comment, upload_time } = row
          let star_repeat = "⭐".repeat(grade)
          let comment_html = `<div class="card">
                          <div class="card-body">
                            <blockquote class="blockquote mb-0">
                              <p>${star_repeat}</p>
                              <p>${comment}</p>
                              <footer class="blockquote-footer">${nick_name} (${upload_time})</footer>
                            </blockquote>
                          </div>
                        </div>`
          $('#comment-list').append(comment_html)
        })
      }

      $('#pagination').empty()
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
    })
  }
