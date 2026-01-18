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
    const lbImg = document.getElementById('lightbox-image');
    
    lbImg.src = img.src;
    
    // 回転状態だけを取得して反映
    const degree = parseInt(img.dataset.rotate || 0);
    
    // ★ scaleの計算はあえて行わず、rotateだけを適用する
    // CSSの object-fit: contain が自動的に比率を保ってくれます
    lbImg.style.transform = `rotate(${degree}deg)`;
    
    overlay.style.display = 'flex';
}

/**
 * ライトボックスを閉じる
 */
function closeLightbox() {
    document.getElementById('lightbox-overlay').style.display = 'none';
}