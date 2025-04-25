# 部署到vercel

部署后,调用报错:

[0425/101030.253786:ERROR:platform_shared_memory_region_posix.cc(217)] Creating shared memory in /dev/shm/.org.chromium.Chromium.l6w2Y5 failed: No such file or directory (2)
[0425/101030.253846:ERROR:platform_shared_memory_region_posix.cc(220)] Unable to access(W_OK|X_OK) /dev/shm: No such file or directory (2)
[0425/101030.253852:FATAL:platform_shared_memory_region_posix.cc(222)] This is frequently caused by incorrect permissions on /dev/shm.  Try 'sudo chmod 1777 /dev/shm' to fix.
Python process exited with signal: 5 (SIGTRAP) (core dumped). The logs above can help with debugging the issue.

这个错误日志表明你的程序在尝试使用共享内存时遇到了权限问题，导致程序崩溃。 让我们逐行分析一下：

[0425/100509.189366:ERROR:platform_shared_memory_region_posix.cc(217)] Creating shared memory in /dev/shm/.org.chromium.Chromium.lt4Z1V failed: No such file or directory (2): 程序尝试在 /dev/shm/.org.chromium.Chromium.lt4Z1V 目录下创建共享内存，但该目录不存在。 /dev/shm 是一个用于共享内存的 POSIX 标准目录，Chromium 系的程序（例如 Chrome, Edge, Electron 应用）经常使用它。 这个错误表明要么 /dev/shm 不存在，要么 /.org.chromium.Chromium.lt4Z1V 目录不存在。

[0425/100509.189418:ERROR:platform_shared_memory_region_posix.cc(220)] Unable to access(W_OK|X_OK) /dev/shm: No such file or directory (2): 程序无法访问 /dev/shm 目录，需要的权限是可写 (W_OK) 和可执行 (X_OK)。 同样，提示目录不存在。

[0425/100509.189422:FATAL:platform_shared_memory_region_posix.cc(222)] This is frequently caused by incorrect permissions on /dev/shm. Try 'sudo chmod 1777 /dev/shm' to fix.: 这是一个致命错误，程序无法继续执行。错误消息明确指出 /dev/shm 的权限不正确，并给出了一个可能的修复方案： sudo chmod 1777 /dev/shm。

Python process exited with signal: 5 (SIGTRAP) (core dumped). The logs above can help with debugging the issue.: 你的 Python 进程因收到 SIGTRAP 信号（通常是由于断点或断言失败）而终止，并生成了 core dump 文件，用于调试。日志建议你根据上面的错误信息来调试。