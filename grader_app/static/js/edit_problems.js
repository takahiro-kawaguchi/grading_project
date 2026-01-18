document.addEventListener('DOMContentLoaded', function() {
    
    const list = document.getElementById('problem-list');

    const sortable = new Sortable(list, {
        handle: '.handle',
        animation: 150
    });

    document.getElementById('addBtn').addEventListener('click', () => {
        const tempId = "q_" + Date.now();
        const html = `
            <li class="list-item" data-id="${tempId}">
                <span class="handle">⠿</span>
                <textarea class="editable problem-text" rows="3"></textarea>
                <button class="btn btn-outline-danger del-btn">削除</button>
            </li>`;
        list.insertAdjacentHTML('beforeend', html);
    });


    list.addEventListener('click', (e) => {
        if (e.target.classList.contains('del-btn')) {
            if (confirm("この問題を削除すると採点結果も失われます。よろしいですか？")) {
                e.target.closest('.list-item').remove();
            }
        }
    });


    const saveBtn = document.getElementById('saveBtn');
    if (saveBtn){
        saveBtn.addEventListener('click', function() {
            if (!confirm('変更を保存しますか？')) {
                return;
            }
            const order = [];
            const problems = {};
            
            document.querySelectorAll('.list-item').forEach(item => {
                const id = item.dataset.id;
                const text = item.querySelector('.problem-text').value;
                order.push(id);
                problems[id] = text;
            });

            const save_destination = this.getAttribute('data-save-url');
            const back_url = this.getAttribute('data-back-url');
            
            fetch(save_destination, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order, problems })
            })
            .then(response => {
                if (response.ok) {
                    // 3. サーバー側での保存が成功した後にリダイレクト
                    // location.replace(back_url) でも location.href = back_url でもOK
                    location.replace(back_url);
                } else {
                    alert("保存中にエラーが発生しました。");
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert("通信に失敗しました。");
            });
        });
    }

    const cancelBtn = document.getElementById('cancelBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            // HTMLの data-back-url から値を取得
            const destination = this.getAttribute('data-back-url');

            if (confirm("変更を破棄してよろしいですか？")) {
                window.location.href = destination;
            }
        });
    }
});



