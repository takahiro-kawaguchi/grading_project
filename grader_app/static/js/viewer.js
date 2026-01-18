/**
 * 設定の読み書き（localStorage）を担当
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

/**
 * 保存処理を管理するオブジェクト（連打対策・整合性維持）
 */
const AutoSaver = {
    timeoutId: null,

    /**
     * 変更を通知し、適切なタイミングで送信を予約する
     */
    trigger() {
        console.log('AutoSaver.trigger called');

        clearTimeout(this.timeoutId);
        this.timeoutId = setTimeout(() => this.send(), 500);

    },

    /**
     * サーバーへデータを送信する（一本道で実行）
     */
    async send() {
        // すでに送信中の場合は、終わった後に再度呼ばれるのでスキップ
        console.log('AutoSaver.send called');

        const form = document.getElementById('problems-form');
        if (!form) return;

        const formData = new FormData(form);
        const grades = {};
        formData.forEach((value, key) => { grades[key] = value; });
        console.log('送信データ:', grades);

        const saveDestination = form.getAttribute('data-save-url');

        try {
            const response = await fetch(saveDestination, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ grades: grades }),
                keepalive: true
            });
            const data = await response.json();
            
            console.log("保存完了:", data);

            // Flask側が「全問題採点済み」を返してきたら遷移チェック
            if (data.status === 'finished') {
                handleAutoTransition();
            }
        } catch (error) {
            console.error("通信エラー:", error);
        }
    },
};

/**
 * 自動遷移のロジック
 */
async function handleAutoTransition() {

    const settings = AppSettings.get();
    if (!settings.isAuto) return;

    if (settings.isConfirm) {
        if (!confirm('全ての問題にマークがつけられました。次のレポートに移動しますか？')) {
            return;
        }
    }

    const nextBtn = document.getElementById("next-unfinished-report-link");
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

    // フォーム内容が変更されたらトリガー
    form.addEventListener('change', () => {
        AutoSaver.trigger();
    });

    // クリアボタン処理（イベントデリゲーション）
    form.addEventListener('click', (e) => {
        const btn = e.target.closest('.clear-btn');
        if (btn) {
            const targetName = btn.getAttribute('data-target');
            const radios = document.getElementsByName(targetName);
            let changed = false;
            radios.forEach(r => {
                if (r.checked) {
                    r.checked = false;
                    changed = true;
                }
            });
            if (changed) AutoSaver.trigger();
        }
    });

    const rows = document.querySelectorAll('#problems-form tbody tr');
    let currentRowIndex = 0;

    const focusRow = (index) => {
        if (index < 0 || index >= rows.length) return;
        
        const row = rows[index];
        rows.forEach(r => r.classList.remove('table-active'));
        row.classList.add('table-active');

        row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        
        const target = row.querySelector('input[type=radio]:checked') || row.querySelector('input[type=radio]');
        if (target) target.focus();
        
        currentRowIndex = index;
    };

    /**
     * ショートカットキーの制御
     */
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'TEXTAREA' || (e.target.tagName === 'INPUT' && e.target.type === 'text')) return;

        const key = e.key;
        const validKeys = ['ArrowDown', 'ArrowUp', '1', '2', '3', '0'];
        if (!validKeys.includes(key)) return;

        e.preventDefault();

        const currentRow = rows[currentRowIndex];
        if (!currentRow) return;

        if (key === 'ArrowDown') {
            focusRow(Math.min(currentRowIndex + 1, rows.length - 1));
        } 
        else if (key === 'ArrowUp') {
            focusRow(Math.max(currentRowIndex - 1, 0));
        } 
        else if (key === '0') {
            const radios = currentRow.querySelectorAll('input[type=radio]');
            let changed = false;
            radios.forEach(r => { if (r.checked) { r.checked = false; changed = true; } });
            if (changed) AutoSaver.trigger();
        } 
        else {
            const vals = { '1': 'circle', '2': 'triangle', '3': 'cross' };
            const radio = currentRow.querySelector(`input[value="${vals[key]}"]`);
            
            if (radio) {
                if (!radio.checked) {
                    radio.checked = true;
                    AutoSaver.trigger();
                }
                
                // 次の行へ移動
                if (currentRowIndex < rows.length - 1) {
                    setTimeout(() => focusRow(currentRowIndex + 1), 50);
                }
            }
        }
    });

    if (rows.length > 0) focusRow(0);
});