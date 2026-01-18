/**
 * 画像を回転させ、親要素の高さとスケールを調整する
 */
function rotateThisImage(element, degreeOffset) {
    const container = element.closest('.image-container');
    const img = container.querySelector('.pdf-image');

    // 1. 角度の更新
    let currentDegree = parseInt(img.dataset.rotate || 0);
    currentDegree += degreeOffset;
    img.dataset.rotate = currentDegree;

    // 2. 状態と比率の取得
    const isHorizontal = (Math.abs(currentDegree) / 90) % 2 === 1;
    const w = img.naturalWidth;
    const h = img.naturalHeight;

    let scale = 1.0;
    let containerHeight = 'auto';

    if (isHorizontal && h > 0) {
        // 横向き時のスケール（親の幅に合わせる）と高さ計算
        scale = w / h;
        const currentWidth = container.offsetWidth;
        containerHeight = (currentWidth * (w / h)) + 'px';
    }

    // 3. 反映
    img.style.transform = `rotate(${currentDegree}deg) scale(${scale})`;
    container.style.height = containerHeight;
}

/**
 * ライトボックスを開く
 */
function openLightbox(img) {
    const overlay = document.getElementById('lightbox-overlay');
    const content = document.getElementById('lightbox-content');
    const lbImg = document.getElementById('lightbox-image');
    
    lbImg.src = img.src;
    
    const degree = parseInt(img.dataset.rotate || 0);
    const isHorizontal = (Math.abs(degree) / 90) % 2 === 1;

    // 初期化
    overlay.scrollTop = 0;
    lbImg.style.transform = `rotate(${degree}deg)`;

    if (isHorizontal) {
        const w = img.naturalWidth;
        const h = img.naturalHeight;
        
        // 1. 横幅いっぱいにした時の「見た目の高さ」を計算
        // 横向きになると、元の幅(w)が高さ(h)の位置に来るため、
        // 画面幅(100vw) × (元の高さ / 元の幅) が表示上の高さになる
        const displayHeight = window.innerWidth * (h / w);
        
        // 2. スケール調整（横幅をピッタリ合わせる）
        const scale = w / h;
        lbImg.style.transform = `rotate(${degree}deg) scale(${scale})`;
        
        // 3. 親の枠を「見た目の高さ」に固定して余白を殺す
        content.style.height = displayHeight + "px";
        content.style.overflow = "hidden";
        
        // 4. 画像を枠の中央に配置
        lbImg.style.marginTop = "0";
        // 表示を中央に寄せるための調整（flexを使うので不要な場合が多いですが念のため）
        content.style.display = "flex";
        content.style.alignItems = "center";
    } else {
        // 縦向きの時は通常通り
        lbImg.style.transform = `rotate(${degree}deg) scale(1.0)`;
        content.style.height = "auto";
        content.style.overflow = "visible";
        content.style.display = "block";
    }
    
    overlay.style.display = 'block';
}
/**
 * ライトボックスを閉じる
 */
function closeLightbox() {
    const overlay = document.getElementById('lightbox-overlay');
    
    overlay.scrollTop = 0;

    // 表示を消す
    overlay.style.display = 'none';
    
    // ★スクロール位置を一番上（0）にリセット
}