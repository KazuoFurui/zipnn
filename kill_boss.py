import re

print("🗡️ 終端記号（NULL）をコードに注入します...")
with open('csrc/zipnn_core_module.c', 'r', encoding='utf-8') as f:
    code = f.read()

# 配列の最後に {NULL, NULL, 0, NULL} を追加する
code = re.sub(
    r'(\{"combine_dtype".*?\},)\s*(\};)', 
    r'\1\n    {NULL, NULL, 0, NULL} /* 魔王の正体（配列の終端記号） */\n\2', 
    code, flags=re.DOTALL
)

with open('csrc/zipnn_core_module.c', 'w', encoding='utf-8') as f:
    f.write(code)
print("✅ 注入完了！")