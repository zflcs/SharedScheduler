
# Abstract

Multithread programing, as a classic model for solving concurrency issues, has numerous advantages and is widely applied, but it also has certain limitations such as high context switching and kernel stack consumption. Currently, mainstream kernel asynchrony is implemented through kernel threads. Based on the above reasons, we have done the following work. 1) We have utilized the Rust programming language to support the coroutine mechanism and built a thread/coroutine concurrency model. Coroutines are defined as the smallest task units and are introduced into the kernel to provide a coordinated task scheduling mechanism (shared scheduler) for both the kernel and user processes.  2) Building upon this, we have used user-level interrupt technology and coroutine mechanisms to modify certain I/O system calls, providing a fully asynchronous environment for user processes. 3) We conducted a comparison test between threads and coroutines on Qemu and FPGA, and found that coroutines have much lower overhead than threads in terms of context switching.


# 1. Introduction & Relative Work

- 介绍当前主流内核对用户态的异步支持，指出主流内核对异步支持的一些缺陷：
	- Linux提供了内核线程来实现用户态异步，但是在用户态使用内核线程来处理IO请求的开销很大。
	- 主流内核提供了IO多路复用的方式（select/poll/epoll）的方式监听多个IO端口，减少开销，但需要用户态单独开一个poll线程来主动询问，然后把事件发送到其他线程进行处理，本质上属于同步IO。
	- 内核内部还是使用的内核线程实现的异步。
- Rust异步编程的机制介绍。
	- 有栈协程和无栈协程的对比。
- 用户态中断技术的介绍
	- 基本原理。
	- 与共享调度器的异步唤醒相结合。


# 2. Design and Implication

## 2.1 Design

- 进程、线程、协程的概念重新定义。
- 调度器设计
	- 进程、线程调度。
	- 协程调度。
- 状态转换模型。
- 调度器提供的接口。
- 使用vdso提供一套统一的调度框架。
## 2.2  Implication

- 异步系统调用的唤醒机制实现（结合用户态中断）。
- 系统调用接口改造。
- 多核并发处理。

# 3. Performance Evaluation
1. 串行环实验。
2. WebServer实验。

# 4. Conclusion & Discussion