#ifndef PTHREAD_H
#define PTHREAD_H
// winsock2.hを先に読み込むことでtimevalの再定義エラーを完全に防ぎます
#include <winsock2.h>
#include <windows.h>

static inline int gettimeofday(struct timeval * tp, void * tzp) {
    if (tp) { tp->tv_sec = 0; tp->tv_usec = 0; }
    return 0;
}

typedef HANDLE pthread_t;
typedef SRWLOCK pthread_mutex_t;
typedef void pthread_mutexattr_t;

// PTHREAD_MUTEX_INITIALIZER のエラーを修正（SRWLOCKを使用）
#define PTHREAD_MUTEX_INITIALIZER SRWLOCK_INIT

static inline int pthread_mutex_init(pthread_mutex_t *mutex, const pthread_mutexattr_t *attr) { InitializeSRWLock(mutex); return 0; }
static inline int pthread_mutex_destroy(pthread_mutex_t *mutex) { return 0; }
static inline int pthread_mutex_lock(pthread_mutex_t *mutex) { AcquireSRWLockExclusive(mutex); return 0; }
static inline int pthread_mutex_unlock(pthread_mutex_t *mutex) { ReleaseSRWLockExclusive(mutex); return 0; }

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
