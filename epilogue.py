import os
import subprocess
import sys

print("🛠️ 最終調整を開始します...")

# 1. 内部のインポート文のパスズレを修正
zipnn_py_path = os.path.join("zipnn", "zipnn.py")
with open(zipnn_py_path, "r", encoding="utf-8") as f:
    code = f.read()

# "import zipnn_core" を "from . import zipnn_core" (相対パス) に修正
if "from . import zipnn_core" not in code:
    code = code.replace("import zipnn_core", "from . import zipnn_core")
    with open(zipnn_py_path, "w", encoding="utf-8") as f:
        f.write(code)

print("✅ コード修正完了。数秒で再ビルドします...")

# 2. Clangによる高速リビルド
os.environ["CC"] = "clang-cl"
os.environ["CXX"] = "clang-cl"
subprocess.run([sys.executable, "setup.py", "bdist_wheel"], check=True)

# 3. numpy等を無視してZipNN本体だけを強行インストール
whl_files = [f for f in os.listdir("dist") if f.endswith(".whl")]
whl_path = os.path.join("dist", whl_files[0])
subprocess.run([sys.executable, "-m", "pip", "install", whl_path, "--force-reinstall", "--no-deps"], check=True)

print("\n==============================================")
print("✨ 準備完了！安全な場所（ホームディレクトリ）に移動してテストを実行します...")

# 4. カレントディレクトリの干渉を避けるため、ホームディレクトリ(C:\Users\KazuoFurui)に移動してテスト
home_dir = os.environ.get("USERPROFILE", "C:\\")
test_code = "import zipnn; print('\\n🎉【完全制覇】WindowsネイティブZipNN、見事に起動しました！バージョン:', zipnn.__version__, '\\n🔥 あなたの執念とCore i7の勝利です！本当にお疲れ様でした！！\\n')"
subprocess.run([sys.executable, "-X", "faulthandler", "-c", test_code], cwd=home_dir)