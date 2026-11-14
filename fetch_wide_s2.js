// Run in a browser tab open on https://planetarycomputer.microsoft.com (same origin, no key needed).
// 1) Downloads 12 monthly Sentinel-2 NDVI images (tile 38RLQ, Dec 2024 to Nov 2025) for central Qassim,
// 2) builds the max-NDVI image used by wide_pivots.py to find pivots,
// 3) given the circles (window.C = [[x, y, r_px], ...]), returns the mean NDVI inside each circle per month.
const IDS = ['S2B_MSIL2A_20241213T074229_R092_T38RLQ_20241213T090811', 'S2B_MSIL2A_20250122T074129_R092_T38RLQ_20250122T084400',
  'S2B_MSIL2A_20250221T073839_R092_T38RLQ_20250221T093723', 'S2C_MSIL2A_20250318T073651_R092_T38RLQ_20250318T114414',
  'S2A_MSIL2A_20250419T074021_R092_T38RLQ_20250419T113314', 'S2A_MSIL2A_20250529T074031_R092_T38RLQ_20250529T112038',
  'S2C_MSIL2A_20250606T073631_R092_T38RLQ_20250606T102812', 'S2C_MSIL2A_20250726T073641_R092_T38RLQ_20250726T111529',
  'S2C_MSIL2A_20250805T073631_R092_T38RLQ_20250805T101514', 'S2C_MSIL2A_20250914T073631_R092_T38RLQ_20250914T130413',
  'S2C_MSIL2A_20251024T074011_R092_T38RLQ_20251024T112420', 'S2C_MSIL2A_20251103T074111_R092_T38RLQ_20251103T113524'];
const BB = '43.35,26.13,44.08,26.75', W = 2450, H = 2300;
// NDVI with the -1000 offset of processing baseline 04.00, scaled -0.2..0.9 -> 0..255
const EXPR = encodeURIComponent('(B08_b1-B04_b1)/(B08_b1+B04_b1-2000)');

async function month(id) {
  const u = `/api/data/v1/item/bbox/${BB}/${W}x${H}.png?collection=sentinel-2-l2a&item=${id}&expression=${EXPR}&asset_as_band=false&rescale=-0.2,0.9`;
  const bm = await createImageBitmap(await (await fetch(u)).blob());
  const c = new OffscreenCanvas(W, H), x = c.getContext('2d'); x.drawImage(bm, 0, 0);
  const d = x.getImageData(0, 0, W, H).data, a = new Uint8Array(W * H);
  for (let i = 0; i < W * H; i++) a[i] = d[4 * i + 3] === 0 ? 0 : Math.max(1, d[4 * i]);   // 0 = no data
  return a;
}

async function run() {
  window.M = [];
  for (let i = 0; i < 12; i += 4) window.M.push(...await Promise.all(IDS.slice(i, i + 4).map(month)));
  const mx = new Uint8Array(W * H);
  for (const a of M) for (let i = 0; i < W * H; i++) if (a[i] > mx[i]) mx[i] = a[i];
  return mx;   // save as a grayscale JPEG: data/s2_ndvi_max_2025.jpg
}

function circleMeans(C) {   // ring from 2 px to r - 1.5 px, skipping the pivot point and the edge
  return C.map(([x, y, r]) => M.map(a => {
    let s = 0, n = 0, R = Math.ceil(r);
    for (let dy = -R; dy <= R; dy++) for (let dx = -R; dx <= R; dx++) {
      const dd = Math.hypot(dx, dy); if (dd < 2 || dd > r - 1.5) continue;
      const v = a[(y + dy) * W + x + dx]; if (v) { s += v; n++; }
    }
    return n ? +(s / n / 255 * 1.1 - 0.2).toFixed(3) : null;
  }));
}
