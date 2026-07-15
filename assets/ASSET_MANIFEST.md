# ASSET MANIFEST — Wing Flap Bird

Sinh boi `scripts/generate_game_assets.py --seed 20260715` (deterministic).
Ky thuat: Pillow, render 4x + LANCZOS, layer fill/outline/shade/
highlight/rim, soft shadow pre-render. KHONG nhung text vao anh.

**License: MIT** (asset tu sinh, phat hanh cung repository).
Khong su dung asset ben thu ba, khong AI image API, chi phi: 0.

| File | Cong dung | Goc (4x) | In-game | Alpha | Nguon |
|---|---|---|---|---|---|
| `assets/art/characters/swallow/idle.png` | swallow idle strip (4 frame 96x80) | 1536x320 | 384x80 | yes | generate_game_assets.py |
| `assets/art/characters/swallow/flap.png` | swallow flap strip (4 frame 96x80) | 1536x320 | 384x80 | yes | generate_game_assets.py |
| `assets/art/characters/swallow/hurt.png` | swallow hurt strip (2 frame 96x80) | 768x320 | 192x80 | yes | generate_game_assets.py |
| `assets/art/characters/duck/idle.png` | duck idle strip (4 frame 96x80) | 1536x320 | 384x80 | yes | generate_game_assets.py |
| `assets/art/characters/duck/flap.png` | duck flap strip (4 frame 96x80) | 1536x320 | 384x80 | yes | generate_game_assets.py |
| `assets/art/characters/duck/hurt.png` | duck hurt strip (2 frame 96x80) | 768x320 | 192x80 | yes | generate_game_assets.py |
| `assets/art/characters/stork/idle.png` | stork idle strip (4 frame 96x80) | 1536x320 | 384x80 | yes | generate_game_assets.py |
| `assets/art/characters/stork/flap.png` | stork flap strip (4 frame 96x80) | 1536x320 | 384x80 | yes | generate_game_assets.py |
| `assets/art/characters/stork/hurt.png` | stork hurt strip (2 frame 96x80) | 768x320 | 192x80 | yes | generate_game_assets.py |
| `assets/art/characters/owl/idle.png` | owl idle strip (4 frame 96x80) | 1536x320 | 384x80 | yes | generate_game_assets.py |
| `assets/art/characters/owl/flap.png` | owl flap strip (4 frame 96x80) | 1536x320 | 384x80 | yes | generate_game_assets.py |
| `assets/art/characters/owl/hurt.png` | owl hurt strip (2 frame 96x80) | 768x320 | 192x80 | yes | generate_game_assets.py |
| `assets/art/characters/sparrow/idle.png` | sparrow idle strip (4 frame 96x80) | 1536x320 | 384x80 | yes | generate_game_assets.py |
| `assets/art/characters/sparrow/flap.png` | sparrow flap strip (4 frame 96x80) | 1536x320 | 384x80 | yes | generate_game_assets.py |
| `assets/art/characters/sparrow/hurt.png` | sparrow hurt strip (2 frame 96x80) | 768x320 | 192x80 | yes | generate_game_assets.py |
| `assets/art/backgrounds/sky.png` | gradient troi (layer 1) | 1000x700 | 1000x700 | no | generate_game_assets.py |
| `assets/art/backgrounds/clouds_far.png` | may rat xa - parallax cham nhat | 4000x880 | 1000x220 | yes | generate_game_assets.py |
| `assets/art/backgrounds/mountains_far.png` | nui xa mau nhat (atmospheric) | 4000x1040 | 1000x260 | yes | generate_game_assets.py |
| `assets/art/backgrounds/clouds_mid.png` | may giua sang hon | 4000x960 | 1000x240 | yes | generate_game_assets.py |
| `assets/art/backgrounds/kites_mid.png` | dieu gio le hoi (diem nhan WIND FESTIVAL) | 4000x1200 | 1000x300 | yes | generate_game_assets.py |
| `assets/art/backgrounds/village_mid.png` | lang + doi lop giua | 4000x960 | 1000x240 | yes | generate_game_assets.py |
| `assets/art/backgrounds/foliage_near.png` | bui la foreground (parallax nhanh) | 4000x600 | 1000x150 | yes | generate_game_assets.py |
| `assets/art/backgrounds/ground_near.png` | mat dat cuon (path + co) | 4000x336 | 1000x84 | yes | generate_game_assets.py |
| `assets/art/obstacles/bamboo_gate_top.png` | cot tre tren (crop theo chieu cao runtime) | 368x2480 | 92x620 | yes | generate_game_assets.py |
| `assets/art/obstacles/bamboo_gate_bottom.png` | cot tre duoi (crop theo chieu cao runtime) | 368x2480 | 92x620 | yes | generate_game_assets.py |
| `assets/art/obstacles/gate_cap.png` | thanh ngang mep khoang trong | 432x136 | 108x34 | yes | generate_game_assets.py |
| `assets/art/obstacles/gate_shadow.png` | shadow mem do ben phai cot | 184x2480 | 46x620 | yes | generate_game_assets.py |
| `assets/art/obstacles/ribbon_red.png` | co lua bay o mep khoang trong | 184x120 | 46x30 | yes | generate_game_assets.py |
| `assets/art/obstacles/ribbon_yellow.png` | co lua bay o mep khoang trong | 184x120 | 46x30 | yes | generate_game_assets.py |
| `assets/art/effects/feather.png` | long roi khi flap | 104x80 | 26x20 | yes | generate_game_assets.py |
| `assets/art/effects/wind_streak.png` | vet gio ngang | 280x64 | 70x16 | yes | generate_game_assets.py |
| `assets/art/effects/sparkle.png` | lap lanh khi ghi diem | 88x88 | 22x22 | yes | generate_game_assets.py |
| `assets/art/effects/flap_ring.png` | vong pulse khi flap | 440x440 | 110x110 | yes | generate_game_assets.py |
| `assets/art/effects/contact_shadow.png` | bong tiep dat duoi nhan vat | 560x160 | 140x40 | yes | generate_game_assets.py |
| `assets/art/ui/panel.png` | panel cream 2.5D (scale theo nhu cau) | 2240x1600 | 560x400 | yes | generate_game_assets.py |
| `assets/art/ui/panel_shadow.png` | shadow panel pre-render | 2240x1600 | 560x400 | yes | generate_game_assets.py |
| `assets/art/ui/button.png` | nut chinh (mango) | 1600x304 | 400x76 | yes | generate_game_assets.py |
| `assets/art/ui/button_pressed.png` | nut nhan xuong | 1600x304 | 400x76 | yes | generate_game_assets.py |
| `assets/art/ui/logo_mark.png` | logo mark (swallow flap) | 384x320 | 192x160 | yes | generate_game_assets.py |
| `assets/art/ui/icons.png` | icon strip 6x40px (play/gear/?/heart/cam/back) | 960x160 | 240x40 | yes | generate_game_assets.py |

Cac asset khac:
- `assets/fonts/BeVietnamPro-*.ttf` — SIL OFL 1.1, tai tu kho phan phoi chinh thuc google/fonts (`ofl/bevietnampro`).
- `assets/support/*.png` — anh QR do developer cung cap (khong sua, khong decode).
- `assets/models/pose_landmarker_lite.task` — Apache-2.0 (MediaPipe).
- `assets/audio/*.wav` — sinh boi `scripts/generate_audio_assets.py`, MIT.
- `assets/icon/*` — sinh boi `scripts/generate_icon.py`, MIT.