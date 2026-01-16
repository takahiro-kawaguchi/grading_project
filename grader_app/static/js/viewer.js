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

// /**
//  * フォームの値を収集してJSONにする
//  */
// function collectFormData() {
//     const getValues = (prefix, count) => 
//         Array.from({ length: count }, (_, i) => form.elements[`${prefix}${i}`]?.value || "");

//     return JSON.stringify({
//         author: author,
//         report: report,
//         problems: getValues('problem', n_problems),
//         common: getValues('common', n_problems_common)
//     });
// }

// /**
//  * メインの保存・遷移処理
//  */
// async function submitForm() {
//     try {
//         const response = await fetch('/save_marks', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: collectFormData()
//         });
//         const data = await response.json();

//         if (data.message === 'finished') {
//             handleAutoTransition();
//         }
//     } catch (error) {
//         console.error("保存失敗:", error);
//     }
// }

/**
 * 自動遷移のロジック
 */
function handleAutoTransition() {
    const settings = AppSettings.get();
    if (!settings.isAuto) return;

    // 確認が必要な設定かつ、ユーザーがキャンセルした場合は中止
    if (settings.isConfirm) {
        if (!confirm('全ての問題にマークがつけられました。次のレポートに移動しますか？')) {
            return;
        }
    }

    const nextUrl = document.getElementById("link-next-unfinished").href;
    // location.replace(nextUrl);
}

// 初期化処理
document.addEventListener('DOMContentLoaded', () => {
    AppSettings.load();
    
    // チェックボックス変更時に自動保存
    document.querySelectorAll('.pref-storage').forEach(el => {
        el.addEventListener('change', () => AppSettings.save());
    });
});



// /**
//  * 1. 設定管理 (localStorage)
//  * URLパラメータを介さず、ブラウザ自体に設定を記憶させます
//  */
// const AppSettings = {
//     keys: {
//         autoTransition: 'pref_auto_transition',
//         confirmRequired: 'pref_confirm_required'
//     },
//     save() {
//         localStorage.setItem(this.keys.autoTransition, document.getElementById("auto-next").checked);
//         localStorage.setItem(this.keys.confirmRequired, document.getElementById("confirm-next").checked);
//     },
//     load() {
//         const auto = localStorage.getItem(this.keys.autoTransition) !== 'false'; // デフォルトtrue
//         const confirm = localStorage.getItem(this.keys.confirmRequired) !== 'false';
//         document.getElementById("auto-next").checked = auto;
//         document.getElementById("confirm-next").checked = confirm;
//         return { auto, confirm };
//     },
//     get() {
//         return {
//             auto: localStorage.getItem(this.keys.autoTransition) !== 'false',
//             confirm: localStorage.getItem(this.keys.confirmRequired) !== 'false'
//         };
//     }
// };

// /**
//  * 2. データの収集と保存
//  */
// function getFormData() {
//     const getValues = (prefix, count) => 
//         Array.from({ length: count }, (_, i) => form.elements[`${prefix}${i}`]?.value || "");

//     return JSON.stringify({
//         author, report,
//         problems: getValues('problem', n_problems),
//         common: getValues('common', n_problems_common)
//     });
// }

// function submitForm() {
//     fetch('/save_marks', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: getFormData()
//     })
//     .then(res => res.json())
//     .then(data => {
//         if (data.message === 'finished') {
//             handleAutoTransition();
//         }
//     });
// }

// /**
//  * 3. 遷移ロジック（ここが一番スッキリします）
//  */
// function handleAutoTransition() {
//     const settings = AppSettings.get();
//     if (!settings.auto) return;

//     if (settings.confirm) {
//         if (!confirm('全ての問題にマークがつけられました。次のレポートに移動しますか？')) {
//             return;
//         }
//     }

//     const nextUrl = document.getElementById("next-unfinished-report-link").href;
//     location.replace(nextUrl);
// }

// /**
//  * 4. UI操作（既存機能を整理）
//  */
// function resetOption(optionName) {
//     document.getElementsByName(optionName).forEach(r => r.checked = false);
//     submitForm();
// }

// // チェックボックス変更時のイベント（URL書き換えの代わり）
// function onSettingChange() {
//     AppSettings.save();
// }

// /**
//  * 5. 初期化とキーボード操作
//  */
// document.addEventListener('DOMContentLoaded', () => {
//     AppSettings.load();
//     const rows = document.querySelectorAll('#problems-form tbody tr');
//     let currentRowIndex = 0;

//     // フォーカス制御
//     const focusRow = (index) => {
//         const row = rows[index];
//         if (!row) return;
        
//         const target = row.querySelector('input[type=radio]:checked') || row.querySelector('input[type=radio]');
//         if (target) target.focus();

//         rows.forEach(r => r.classList.remove('table-active'));
//         row.classList.add('table-active');
//     };

//     // ショートカットキー
//     document.addEventListener('keydown', (e) => {
//         if (['ArrowDown', 'ArrowUp', '1', '2', '3', '0'].includes(e.key)) {
//             if (e.key === 'ArrowDown') currentRowIndex = Math.min(currentRowIndex + 1, rows.length - 1);
//             else if (e.key === 'ArrowUp') currentRowIndex = Math.max(currentRowIndex - 1, 0);
//             else if (e.key === '0') resetOption(rows[currentRowIndex].querySelector('input').name);
//             else {
//                 const vals = { '1': 'circle', '2': 'triangle', '3': 'cross' };
//                 const radios = rows[currentRowIndex].querySelectorAll('input[type=radio]');
//                 radios.forEach(r => { if (r.value === vals[e.key]) r.checked = true; });
                
//                 if (currentRowIndex < rows.length - 1) {
//                     currentRowIndex++;
//                 }
//                 submitForm();
//             }
//             focusRow(currentRowIndex);
//             e.preventDefault();
//         }
//     });

//     // ラジオボタンのクリックイベント一括設定
//     document.querySelectorAll('input[type="radio"]').forEach(r => {
//         r.addEventListener('change', submitForm);
//     });

//     focusRow(0);
// });