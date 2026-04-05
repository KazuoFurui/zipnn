import os
import subprocess
import sys

print("🚀 最終ビルドシーケンスを開始します...")

# 1. 壊れたCコードを元に戻し、安全なパッチだけを確実に適用
print("🧹 Cコードをクリーンアップ＆安全パッチ適用中...")
os.system("git checkout csrc/zipnn_core.c")
with open("csrc/zipnn_core.c", "r", encoding="utf-8") as f:
    code = f.read()

# pthreadの偽装と、クラッシュの原因になるvoid*ポインタの安全化
code = code.replace('<pthread.h>', '"pthread.h"').replace('<sys/time.h>', '"pthread.h"')
code = code.replace('thread_data->data->buf + offset', '(uint8_t *)thread_data->data->buf + offset')

with open("csrc/zipnn_core.c", "w", encoding="utf-8") as f:
    f.write(code)

# 2. 正しい setup.py を自動生成（モジュール名を zipnn.zipnn_core に修正！）
print("📝 正しい setup.py を生成中...")
setup_content = """from setuptools import setup, find_packages, Extension
import sys, os

compile_args = ["/O2", "/MD"] if sys.platform.startswith("win") else ["-O3"]
zipnn_core_ext = Extension(
    "zipnn.zipnn_core",  # <--- ここがクラッシュの真の原因でした！
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
    description="ZipNN Windows Fork",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(include=["zipnn", "zipnn.*"]),
    ext_modules=[zipnn_core_ext],
    install_requires=['numpy>=1.17.0', 'safetensors>=0.4.0', 'torch>=2.0.0'],
)
"""
with open("setup.py", "w", encoding="utf-8") as f:
    f.write(setup_content)

# 3. Pythonの内部から強制的にClang-CLコンパイラを指定
os.environ["CC"] = "clang-cl"
os.environ["CXX"] = "clang-cl"

# 4. 古いビルドの残骸を削除してクリーンビルド
print("🔨 Clang-CLでコンパイルを開始します（数秒かかります）...")
subprocess.run([sys.executable, "setup.py", "clean", "--all"], capture_output=True)
subprocess.run([sys.executable, "setup.py", "bdist_wheel"], check=True)

# 5. 生成されたWheelを強制再インストール
whl_files = [f for f in os.listdir("dist") if f.endswith(".whl")]
whl_path = os.path.join("dist", whl_files[0])

print(f"📦 パッケージ {whl_files[0]} をインストール中...")
subprocess.run([sys.executable, "-m", "pip", "install", whl_path, "--force-reinstall", "--no-cache-dir"], check=True)

print("✨ すべての工程が完了しました！")