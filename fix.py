import re

# 1. Windows用の超軽量pthread.h（偽装ファイル）を作成
# これによりLinuxのマルチスレッドコードがそのままWindowsのネイティブスレッドで動きます
shim = """#ifndef PTHREAD_H
#define PTHREAD_H
#include <windows.h>
#include <malloc.h>
#include <time.h>

struct timeval { long tv_sec; long tv_usec; };
static inline int gettimeofday(struct timeval * tp, void * tzp) { tp->tv_sec = 0; tp->tv_usec = 0; return 0; }

typedef HANDLE pthread_t;
typedef CRITICAL_SECTION pthread_mutex_t;
typedef void pthread_mutexattr_t;

static inline int pthread_mutex_init(pthread_mutex_t *mutex, const pthread_mutexattr_t *attr) { InitializeCriticalSection(mutex); return 0; }
static inline int pthread_mutex_destroy(pthread_mutex_t *mutex) { DeleteCriticalSection(mutex); return 0; }
static inline int pthread_mutex_lock(pthread_mutex_t *mutex) { EnterCriticalSection(mutex); return 0; }
static inline int pthread_mutex_unlock(pthread_mutex_t *mutex) { LeaveCriticalSection(mutex); return 0; }

typedef struct { void *(*start_routine)(void*); void *arg; } pthread_wrapper_arg;
static DWORD WINAPI pthread_wrapper_func(LPVOID lpParam) {
    pthread_wrapper_arg *p = (pthread_wrapper_arg*)lpParam;
    void *(*func)(void*) = p->start_routine;
    void *arg = p->arg;
    free(p);
    func(arg);
    return 0;
}

static inline int pthread_create(pthread_t *thread, const void *attr, void *(*start_routine)(void*), void *arg) {
    pthread_wrapper_arg *p = (pthread_wrapper_arg*)malloc(sizeof(pthread_wrapper_arg));
    if (!p) return 1;
    p->start_routine = start_routine; p->arg = arg;
    *thread = CreateThread(NULL, 0, pthread_wrapper_func, p, 0, NULL);
    return (*thread == NULL) ? 1 : 0;
}

static inline int pthread_join(pthread_t thread, void **retval) { WaitForSingleObject(thread, INFINITE); CloseHandle(thread); return 0; }
static inline void pthread_exit(void *retval) { ExitThread(0); }
#endif
"""

with open("csrc/pthread.h", "w", encoding="utf-8") as f:
    f.write(shim)

# 2. zipnn_core.c のパッチ当て
with open("csrc/zipnn_core.c", "r", encoding="utf-8") as f:
    code = f.read()

# MSVCでエラーになる可変長配列(VLA)を _alloca に変換
code = re.sub(r'size_t\s+localOffsets\[numBuf\];', r'size_t *localOffsets = (size_t*)_alloca(numBuf * sizeof(size_t));', code)

# インクルードをローカルの偽装ファイルに差し替え
code = code.replace('<pthread.h>', '"pthread.h"')
code = code.replace('<sys/time.h>', '"pthread.h"')

# 先頭に malloc.h を追加
if '<malloc.h>' not in code:
    code = "#include <malloc.h>\n" + code

with open("csrc/zipnn_core.c", "w", encoding="utf-8") as f:
    f.write(code)

print("✅ パッチ適用完了！これでWindowsでコンパイルできます！")