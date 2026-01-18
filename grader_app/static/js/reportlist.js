document.addEventListener('DOMContentLoaded', async () => {
  // 1. 対象となる全要素を取得
  const statusElements = document.querySelectorAll('.status-text');

  // 2. for...of ループで一つずつ順番に処理
  for (const el of statusElements) {
    const url = el.dataset.checkUrl; // HTMLの data-check-url を取得
    const statusId = el.id;

    try {
      // fetchが完了するまで次のループへは進みません
      const response = await fetch(url);
      
      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();

      // 3. 結果に応じて表示を更新
      // 例: サーバーが { "finished": true } のようなJSONを返すと想定
      if (data.all_finished) {
        el.innerHTML = '<i class="bi bi-check-square-fill"></i>';
        el.classList.remove('text-secondary');
        el.classList.add('text-success');
      } else {
        el.innerHTML = '';
        el.classList.remove('text-secondary');
      }

    } catch (error) {
      console.error(`エラー発生 (${statusId}):`, error);
      el.innerHTML = '<i class="bi bi-exclamation-triangle text-danger"></i> エラー';
    }
  }
});
