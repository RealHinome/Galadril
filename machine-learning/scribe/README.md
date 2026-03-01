# Galadril Scribe

> Galadril Scribe is the automatic technical writer of Galadril.

Based on heterogenous data, Sribe writes custom LaTeX report using LLMs, and 
retrives datas using function calls.

Your system needs: fontconfig freetype graphite2 harfbuzz icu4c libpng openssl
zlib

On Mac:
```bash
brew install harfbuzz graphite2 freetype icu4c pkg-config
export PKG_CONFIG_PATH="/opt/homebrew/opt/icu4c/lib/pkgconfig:$PKG_CONFIG_PATH" 
export PKG_CONFIG_PATH="/opt/homebrew/opt/harfbuzz/lib/pkgconfig:\
/opt/homebrew/opt/graphite2/lib/pkgconfig:\
/opt/homebrew/opt/icu4c/lib/pkgconfig:\
/opt/homebrew/opt/freetype/lib/pkgconfig:\
$PKG_CONFIG_PATH"
export CPATH="/opt/homebrew/include"
export LIBRARY_PATH="/opt/homebrew/lib"
```
