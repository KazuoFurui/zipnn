import os
import subprocess
import sys
import re

print("==============================================")
print("🚀 真・最終ビルドシーケンス（モンキーパッチ版）")
print("==============================================")

# 1. 確実なパッチ当て（gitリセットはせずに上書き）
print("[1/4] Cコードのバグを確実に修正中...")
with open("csrc/zipnn_core.c", "r", encoding="utf-8") as f:
    core_code = f.read()

core_code = core_code.replace('<pthread.h>', '"pthread.h"').replace('<sys/time.h>', '"pthread.h"')
core_code = core_code.replace('thread_data->data->buf + offset', '(uint8_t *)thread_data->data->buf + offset')

with open("csrc/zipnn_core.c", "w", encoding="utf-8") as f:
    f.write(core_code)

with open("csrc/zipnn_core_module.c", "r", encoding="utf-8") as f:
    mod_code = f.read()

if "{NULL, NULL, 0, NULL}" not in mod_code:
    mod_code = re.sub(
        r'(\{"combine_dtype".*?\},)\s*(\};)',
        r'\1\n    {NULL, NULL, 0, NULL} /* 真の魔王討伐（終端記号） */\n\2',
        mod_code, flags=re.DOTALL
    )
    with open("csrc/zipnn_core_module.c", "w", encoding="utf-8") as f:
        f.write(mod_code)

# 2. ビルドシステムを騙す最強の setup.py を生成
print("[2/4] setuptoolsハッキング用の setup.py を生成...")
setup_content = """from setuptools import setup, find_packages, Extension
import sys

# 🔥 魔法のモンキーパッチ：cl.exeが呼ばれる瞬間にclang-clにすり替える 🔥
if sys.platform.startswith("win"):
    import distutils._msvccompiler
    old_spawn = distutils._msvccompiler.MSVCCompiler.spawn
    def clang_spawn(self, cmd, **kwargs):
        if isinstance(cmd, list) and len(cmd) > 0:
            if 'cl.exe' in cmd[0] or cmd[0] == 'cl':
                cmd[0] = 'clang-cl'  # 強制すり替え
        return old_spawn(self, cmd, **kwargs)
    distutils._msvccompiler.MSVCCompiler.spawn = clang_spawn

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

# 3. 古い残骸を消去し、クリーンビルド
print("[3/4] Clang-CLによる強制ビルドを開始（数秒待ちます）...")
subprocess.run([sys.executable, "setup.py", "clean", "--all"], capture_output=True)
subprocess.run([sys.executable, "setup.py", "bdist_wheel"], check=True)

# 4. 生成された最新のWheelをインストール
print("[4/4] 完璧なモジュールをインストール中...")
whl_files = [f for f in os.listdir("dist") if f.endswith(".whl")]
whl_path = os.path.join("dist", whl_files[0])
subprocess.run([sys.executable, "-m", "pip", "install", whl_path, "--force-reinstall", "--no-cache-dir"], check=True)

print("\n==============================================")
print("✨ ビルド完全成功！ 運命のテストを実行します...")
print("==============================================")

# 5. カレントディレクトリの干渉を避けるため、ホームディレクトリに移動してテスト実行
test_code = "import zipnn; print('\\n🎉【完全制覇】WindowsネイティブZipNN、見事に起動しました！バージョン:', zipnn.__version__, '\\n🔥 あなたの執念の勝利です！本当にお疲れ様でした！！\\n')"
subprocess.run([sys.executable, "-X", "faulthandler", "-c", test_code], cwd=os.path.expanduser("~"))