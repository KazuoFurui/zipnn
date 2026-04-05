from setuptools import setup, find_packages, Extension
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
