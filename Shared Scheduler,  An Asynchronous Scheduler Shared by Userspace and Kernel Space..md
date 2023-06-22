
# Abstract

Multithread programing, as a classic model for solving concurrency issues, has numerous advantages and is widely applied, but it also has certain limitations such as high context switching and kernel stack consumption. Currently, mainstream kernel asynchrony is implemented through kernel threads. Based on the above reasons, we have done the following work. 1) We have utilized the Rust programming language to support the coroutine mechanism and built a thread/coroutine concurrency model. User coroutines are regarded as a fundamental factor for measuring scheduling by the kernel, which improves the overall utilization of system resources.2) Coroutines were introduced into the kernel as the basic unit of scheduling, and a universal asynchronous processing mechanism was built in the kernel. 3) Some IO system calls have been transformed into asynchronous calls by utilizing user-space interrupts. 4) The scheduler is modular and the same set of scheduling code is reused in both user and kernel space through the use of vDSO. We conducted a comparison test between threads and coroutines on Qemu and FPGA, and found that coroutines have much lower overhead than threads in terms of context switching.


# 1. Introduction & Relative Work

- 介绍当前主流内核对用户态的异步支持，指出主流内核对异步支持的一些缺陷：
	- 当前主流的宏内核中，协程仍然作为一种用户态管理的调度单位（例如tokio），无法被内核感知到，内核无法从系统层面对协程进行精细化管理。
	- 内核中缺乏轻量级的异步任务调度方案。内核往往也需要处理如设备读写等异步任务，近年的工作往往是提出一套独立于内核线程调度之外的单独的异步任务调度方案，首先是没有很好的通用性，其次也增加了内核的复杂度。
	- 在内核和用户态都需要异步调度、且调度特征大体相似的情况下，没有一个统一的、模块化的调度框架同时提供给用户程序和内核。
- Rust异步编程的机制介绍。
	- 有栈协程和无栈协程的对比。
- 用户态中断技术的介绍
	- 基本原理。
	- 与共享调度器的异步唤醒相结合。


# 2. Design and Implementation

## 2.1 Design
- 系统框架。
- 进程、线程、协程的概念重新定义。
- 调度器设计
	- 协程调度。
	- 进程、线程调度。
- 状态转换模型。
- 调度器提供的接口。
## 2.2  Implementation

- 局部优先级和全局优先级。
- 异步系统调用实现
	- 接口改造
	- 异步系统调用的唤醒机制实现（结合用户态中断）。
- 用户态中断唤醒的同步互斥的问题
- 兼容性实现
	- 用户态的代码入口为调度器初始化代码，为用户提供完全异步的环境。
	- 内核态的线程调度和协程调度的统一。
- 模块化调度器，用vdso在用户态和内核态复用了同一套调度代码。

# 3. Performance Evaluation
1. 用户态和内核态的优先级串口实验。
2. WebServer实验。
	1. 协程的切换开销远低于线程。
	2. 优先级在资源有限的情况下，保证某些任务能够高效完成。

# 4. Conclusion
- 总结本文工作，重申实验结论。
	- 将协程作为内核衡量调度的因素，提升系统资源的整体利用率。
	- 将协程引入内核并作为内核调度的基本单位，在内核构建了一套通用的异步处理机制。
	- 协程优先级。
	- 利用用户态中断对IO系统调用进行了异步化改造。
	- 实验结论。