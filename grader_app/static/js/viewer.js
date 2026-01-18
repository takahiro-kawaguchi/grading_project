/**
 * 設定の読み書き（localStorage）を担当するオブジェクト
 */
const AppSettings = {
    keys: {
        auto: 'setting_auto_transition',
        confirm: 'setting_confirm_required'
    },
    save() {
        localStorage.setItem(this.keys.auto, document.getElementById('setting-auto-transition').checked);
        localStorage.setItem(this.keys.confirm, document.getElementById('setting-confirm-required').checked);
    },
    load() {
        document.getElementById('setting-auto-transition').checked = localStorage.getItem(this.keys.auto) === 'true';
        document.getElementById('setting-confirm-required').checked = localStorage.getItem(this.keys.confirm) === 'true';
    },
    get() {
        return {
            isAuto: localStorage.getItem(this.keys.auto) === 'true',
            isConfirm: localStorage.getItem(this.keys.confirm) === 'true'
        };
    }
};

let timeoutId = null;
let isDirty = false; // 未保存の変更があるかどうかのフラグ

/**
 * Flaskへデータを送信するメイン関数
 */
async function sendGradesToServer() {
    const form = document.getElementById('problems-form');
    if (!form || !isDirty) return;

    const formData = new FormData(form);
    const grades = {};
    formData.forEach((value, key) => {
        grades[key] = value;
    });

    const saveDestination = form.getAttribute('data-save-url');

    try {
        const response = await fetch(saveDestination, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ grades: grades }),
            keepalive: true // ページ遷移時もブラウザが送信を継続する
        });
        const data = await response.json();
        
        isDirty = false; // 保存成功
        console.log("保存完了:", data);

        // Flask側が「全問題採点済み」というステータスを返してきたら遷移チェック
        if (data.status === 'finished') {
            handleAutoTransition();
        }
    } catch (error) {
        console.error("通信エラー:", error);
    }
}

/**
 * 自動遷移のロジック
 */
function handleAutoTransition() {
    const settings = AppSettings.get();
    if (!settings.isAuto) return;

    if (settings.isConfirm) {
        if (!confirm('全ての問題にマークがつけられました。次のレポートに移動しますか？')) {
            return;
        }
    }

    const nextBtn = document.getElementById("link-next-unfinished");
    if (nextBtn && nextBtn.href) {
        location.href = nextBtn.href;
    }
}

// 初期化処理
document.addEventListener('DOMContentLoaded', () => {
    AppSettings.load();
    
    // 設定変更時のイベント
    document.querySelectorAll('.pref-storage').forEach(el => {
        el.addEventListener('change', () => AppSettings.save());
    });

    const form = document.getElementById('problems-form');
    if (!form) return;

    // フォーム内容が変更されたらデバウンス開始
    form.addEventListener('change', () => {
        isDirty = true;
        clearTimeout(timeoutId);
        timeoutId = setTimeout(sendGradesToServer, 500); // 0.5秒後に送信予約
    });

    // ★ ページを離れる（隠れる）瞬間に、未保存があれば即実行
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden' && isDirty) {
            sendGradesToServer();
        }
    });

    form.addEventListener('click', (e) => {
        // クリックされた要素が clear-btn クラスを持っているか確認
        if (e.target.closest('.clear-btn')) {
            const btn = e.target.closest('.clear-btn');
            const targetName = btn.getAttribute('data-target');
            
            // 指定された name のラジオボタンをすべて未選択にする
            const radios = document.getElementsByName(targetName);
            let changed = false;
            radios.forEach(r => {
                if (r.checked) {
                    r.checked = false;
                    changed = true;
                }
            });

            // 状態が変わった場合のみ、isDirtyを立ててデバウンス保存を実行
            if (changed) {
                isDirty = true;
                clearTimeout(timeoutId);
                timeoutId = setTimeout(sendGradesToServer, 500);
            }
        }
    });

    const rows = document.querySelectorAll('#problems-form tbody tr');
    let currentRowIndex = 0;

    /**
     * 指定した行にフォーカス（視覚的強調）を当てる
     */
    const focusRow = (index) => {
        if (index < 0 || index >= rows.length) return;
        
        const row = rows[index];
        rows.forEach(r => r.classList.remove('table-active'));
        row.classList.add('table-active');

        // 画面外に隠れないようスクロール
        row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        
        // ラジオボタンにフォーカスを当てる（アクセシビリティのため）
        const target = row.querySelector('input[type=radio]:checked') || row.querySelector('input[type=radio]');
        if (target) target.focus();
        
        currentRowIndex = index;
    };

    /**
     * ショートカットキーの制御
     */
    document.addEventListener('keydown', (e) => {
        // 入力中のテキストエリアなどがある場合は無効化
        if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT' && e.target.type === 'text') return;

        const key = e.key;
        const validKeys = ['ArrowDown', 'ArrowUp', '1', '2', '3', '0'];
        if (!validKeys.includes(key)) return;

        e.preventDefault(); // ブラウザ標準のスクロールなどを防止

        const currentRow = rows[currentRowIndex];
        if (!currentRow) return;

        if (key === 'ArrowDown') {
            focusRow(Math.min(currentRowIndex + 1, rows.length - 1));
        } 
        else if (key === 'ArrowUp') {
            focusRow(Math.max(currentRowIndex - 1, 0));
        } 
        else if (key === '0') {
            // クリア処理
            const radios = currentRow.querySelectorAll('input[type=radio]');
            let changed = false;
            radios.forEach(r => { if (r.checked) { r.checked = false; changed = true; } });
            if (changed) triggerChange();
        } 
        else {
            // 1=circle, 2=triangle, 3=cross
            const vals = { '1': 'circle', '2': 'triangle', '3': 'cross' };
            const targetVal = vals[key];
            const radio = currentRow.querySelector(`input[value="${targetVal}"]`);
            
        if (radio) {
                // すでにチェックされていれば保存は走らせないが、
                // チェックされていなければチェックして保存を予約
                if (!radio.checked) {
                    radio.checked = true;
                    triggerChange();
                }
                
                // ★ 状態の変更有無に関わらず、次の行へ移動する
                if (currentRowIndex < rows.length - 1) {
                    // 視覚的なフィードバックのために、ごくわずかに遅延させて移動
                    setTimeout(() => focusRow(currentRowIndex + 1), 50);
                } else {
                    // 最後の行なら、完了の自動遷移をチェックするために即送信
                    // (デバウンスを待たずに送信したい場合)
                    // sendGradesToServer(); 
                }
            }
        }
    });

    /**
     * プログラムからの変更を検知させるための補助関数
     */
    function triggerChange() {
        isDirty = true;
        clearTimeout(timeoutId);
        timeoutId = setTimeout(sendGradesToServer, 500);
    }

    // 最初に一行目を選択状態にする
    if (rows.length > 0) focusRow(0);


});