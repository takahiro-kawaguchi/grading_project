document.addEventListener('DOMContentLoaded', () => {

    const fetchURL = document.getElementById('student-list').getAttribute('data-check-url');

    fetch(fetchURL)
            .then(response => response.json())
            .then(dataList => {
                // dataList は [true, false, true, ...] のような配列
                console.log(dataList);
                dataList.finished.forEach((isFinished, index) => {
                    // index (0, 1, 2...) を使ってDOM要素を取得
                    const statusText = document.getElementById(`status-${index}`);
                    
                    if (!statusText) return; // 要素がなければスキップ

                    if (isFinished) {
                        statusText.innerHTML = '<i class="bi bi-check-square-fill"></i>';
                        statusText.classList.remove('text-secondary');
                        statusText.classList.add('text-success');
                    } else {
                        // 未完了の場合の処理（空にする、あるいは未完了アイコンを出す等）
                        statusText.innerHTML = '';
                        statusText.classList.remove('text-secondary');
                    }
                });
            })
            .catch(error => console.error('Error:', error));

});