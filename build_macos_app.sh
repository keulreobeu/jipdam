#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP="$ROOT/집담.app"
CONTENTS="$APP/Contents"
MACOS="$CONTENTS/MacOS"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "이 빌드 파일은 macOS에서 실행해야 합니다."
  exit 1
fi
command -v osacompile >/dev/null || { echo "Xcode Command Line Tools가 필요합니다."; exit 1; }

mkdir -p "$MACOS"
cat > "$MACOS/집담" <<'LAUNCHER'
#!/bin/zsh
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
open -a Terminal "$ROOT/jipdam-mac.command"
LAUNCHER
chmod +x "$MACOS/집담"
cat > "$CONTENTS/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>집담</string>
<key>CFBundleIdentifier</key><string>kr.jipdam.launcher</string>
<key>CFBundleName</key><string>집담</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>12.0</string>
</dict></plist>
PLIST
echo "생성 완료: $APP"
echo "앱은 같은 폴더의 집담 프로젝트와 jipdam-mac.command를 실행합니다."
