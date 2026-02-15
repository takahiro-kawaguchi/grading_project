document.addEventListener('DOMContentLoaded', async () => {
  const inputs = document.querySelectorAll('.score-input');
  if (inputs.length > 0) {
    inputs.forEach(input => {
      input.addEventListener('input', updateTableEffect);
    });
    // 初回表示時にも一度計算
    updateTableEffect();
  }
});

/**
 * テーブルの色と評価、および統計サマリーを更新する関数
 */
// updateTableEffect 関数を以下のように書き換え
function updateTableEffect() {
  const s = parseInt(document.getElementById('threshold-s')?.value) || 0;
  const a = parseInt(document.getElementById('threshold-a')?.value) || 0;
  const b = parseInt(document.getElementById('threshold-b')?.value) || 0;
  const c = parseInt(document.getElementById('threshold-c')?.value) || 0;

  // 評価判定用のヘルパー関数
  const getGrade = (score) => {
    if (score >= s) return 'S';
    if (score >= a) return 'A';
    if (score >= b) return 'B';
    if (score >= c) return 'C';
    return 'D';
  };

  // 1. すべてのスコアセル（個別点数 + 平均点）の色を更新
  document.querySelectorAll('.score-cell, .average-score-cell').forEach(td => {
    const score = parseFloat(td.innerText);
    if (isNaN(score)) return;

    const grade = getGrade(score);
    // 既存の grade-text-* クラスを削除して付け直し
    td.classList.forEach(cls => { if(cls.startsWith('grade-text-')) td.classList.remove(cls); });
    td.classList.add(`grade-text-${grade}`);
  });

  // 2. 評価列の文字と統計の計算
  let counts = { S: 0, A: 0, B: 0, C: 0, D: 0 };
  const avgCells = document.querySelectorAll('.average-score-cell');

  avgCells.forEach(td => {
    const score = parseFloat(td.innerText);
    const grade = getGrade(score);
    counts[grade]++;

    // 評価セルの文字更新
    const row = td.closest('tr');
    const gradeCell = row.querySelector('.grade-cell');
    if (gradeCell) {
        gradeCell.innerText = grade;
        gradeCell.classList.forEach(cls => { if(cls.startsWith('grade-text-')) gradeCell.classList.remove(cls); });
        gradeCell.classList.add(`grade-text-${grade}`);
    }
  });

  // 3. 統計サマリーの更新（前回と同じ）
  const total = avgCells.length;
  for (const [grade, count] of Object.entries(counts)) {
    const countEl = document.getElementById(`stat-count-${grade}`);
    const ratioEl = document.getElementById(`stat-ratio-${grade}`);
    if (countEl) countEl.innerText = count;
    if (ratioEl) {
      const ratio = total > 0 ? (count / total * 100).toFixed(1) : 0;
      ratioEl.innerText = ratio + '%';
    }
  }
}

/**
 * 設定をサーバーに永久保存する（ボタンから呼び出す）
 */
async function saveThresholds() {
  const data = {
    s: document.getElementById('threshold-s').value,
    a: document.getElementById('threshold-a').value,
    b: document.getElementById('threshold-b').value,
    c: document.getElementById('threshold-c').value,
    delay_threshold_days: document.getElementById('delay-threshold-days').value,
    ratio_detail_only: document.getElementById('ratio-detail-only').value,
    ratio_answer_only: document.getElementById('ratio-answer-only').value,
    ratio_duplicate: document.getElementById('ratio-duplicate').value,
    ratio_late: document.getElementById('ratio-late').value,
    ratio_very_late: document.getElementById('ratio-very-late').value
  };

  try {
    const response = await fetch("/pdf/save_thresholds/", { // Blueprint名に合わせて調整
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (response.ok) {
      alert('設定を保存しました。再計算して表示します。');
      location.reload(); 
    } else {
      alert('保存に失敗しました。');
    }
  } catch (error) {
    console.error('Save error:', error);
    alert('通信エラーが発生しました。');
  }
}
