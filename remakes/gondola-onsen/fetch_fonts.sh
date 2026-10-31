#!/usr/bin/env bash
# Google Fonts からフルセットのフォントを取得して fonts/ を置き換える
set -euo pipefail
cd "$(dirname "$0")/fonts"
get() { url=$(curl -sS "https://fonts.googleapis.com/css2?family=$1" | grep -o 'https://[^)]*' | head -1); curl -sS -o "$2" "$url"; echo "fetched $2"; }
get "Noto+Sans+JP:wght@900" jp-black.ttf
get "Noto+Sans+JP:wght@500" jp-medium.ttf
get "Shippori+Mincho:wght@800" mincho.ttf
get "Orbitron:wght@800" orbitron.ttf
