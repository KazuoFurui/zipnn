import os
import subprocess
import sys
import re

print("==============================================")
print("🗡️ 魔王討伐＆最終ビルド 全自動スクリプト")
print("==============================================")

# 1. Cコードのクリーンアップとパッチ当て
print("[1/4] Cコードの修復と安全化...")
os.system("git checkout csrc/zipnn_core.c")
with open("csrc/zipnn_core.c", "r", encoding="utf-8") as f:
    core_code = f.read()

core_code = core_code.replace('<pthread.h>', '"pthread.h"').replace('<sys/time.h>', '"pthread.h"')
core_code = core_code.replace('thread_data->data->buf + offset', '(uint8_t *)thread_data->data->buf + offset')

with open("csrc/zipnn_core.c", "w", encoding="utf-8") as f:
    f.write(core_code)

# 2. 魔王の正体（配列の終端記号）の確実な注入
print("[2/4] 初期化配列のバグ（0x1クラッシュの原因）を修正...")
os.system("git checkout csrc/zipnn_core_module.c")
with open("csrc/zipnn_core_module.c", "r", encoding="utf-8") as f:
    mod_code = f.read()

# すでに修正済みでなければ追加
if "{NULL, NULL, 0, NULL}" not in mod_code:
    mod_code = re.sub(
        r'(\{"combine_dtype".*?\},)\s*(\};)',
        r'\1\n    {NULL, NULL, 0, NULL} /* 終端記号 */\n\2',
        mod_code, flags=re.DOTALL
    )
    with open("csrc/zipnn_core_module.c", "w", encoding="utf-8") as f:
        f.write(mod_code)

# 3. setup.pyの生成（正しいモジュール名）
print("[3/4] ビルド設定の生成...")
setup_content = """from setuptools import setup, find_packages, Extension
import sys
compile_args = ["/O2", "/MD"] if sys.platform.startswith("win") else ["-O3"]
zipnn_core_ext = Extension(
    "zipnn.zipnn_core",
    sources=[
        "csrc/zipnn_core_module.c", "csrc/zipnn_core.c",
        "csrc/data_manipulation_dtype16.c", "csrc/data_manipulation_dtype32.c",
        "include/FiniteStateEntropy/lib/fse_compress.c",
        "include/FiniteStateEntropy/lib/fse_decompress.c",
        "include/FiniteStateEntropy/lib/huf_compress.c",
        "include/FiniteStateEntropy/lib/huf_decompress.c",
        "include/FiniteStateEntropy/lib/entropy_common.c",
        "include/FiniteStateEntropy/lib/hist.c",
    ],
    include_dirs=["include/FiniteStateEntropy/lib/", "csrc/"],
    extra_compile_args=compile_args,
)
setup(
    name="zipnn", version="0.5.3",
    packages=find_packages(include=["zipnn", "zipnn.*"]),
    ext_modules=[zipnn_core_ext],
    install_requires=['numpy>=1.17.0', 'safetensors>=0.4.0', 'torch>=2.0.0'],
)
"""
with open("setup.py", "w", encoding="utf-8") as f:
    f.write(setup_content)

# 4. コンパイル＆インストール
print("[4/4] Clangによるリビルドとインストール（数秒かかります）...")
os.environ["CC"] = "clang-cl"
os.environ["CXX"] = "clang-cl"

# 古いキャッシュを消して確実にリビルド
subprocess.run([sys.executable, "setup.py", "clean", "--all"], capture_output=True)
subprocess.run([sys.executable, "setup.py", "bdist_wheel"], check=True)

whl_files = [f for f in os.listdir("dist") if f.endswith(".whl")]
whl_path = os.path.join("dist", whl_files[0])

subprocess.run([sys.executable, "-m", "pip", "install", whl_path, "--force-reinstall", "--no-cache-dir"], check=True)

print("\n==============================================")
print("✨ すべての工程が完了しました！最終テストを実行します...")

# 5. 運命のテスト実行（ローカルフォルダの干渉を防ぐため、ホームディレクトリで実行）
test_code = "import zipnn; print('\\n🎉【完全制覇】WindowsネイティブZipNN、見事に起動しました！バージョン:', zipnn.__version__, '\\n長い戦い、本当にお疲れ様でした！！\\n')"
subprocess.run([sys.executable, "-X", "faulthandler", "-c", test_code], cwd=os.path.expanduser("~"))