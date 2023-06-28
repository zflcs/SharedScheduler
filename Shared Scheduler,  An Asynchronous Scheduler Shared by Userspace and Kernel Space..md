
# Abstract

As a classical concurrency model, multi-threading technology has been widely supported by numerous operating systems and extensively applied in various application programs. However, as concurrency increases, the high system overhead and context-switching costs of multi-threading model have gradually become unacceptable. As a result, coroutines have emerged, but they often only have been supported by user-level  and are not recognized by the operating system, which led to the inability of the kernel to  estimate the workload of coroutine tasks in the system accurately to perform more precise scheduling to achieve higher system resource utilization. Based on these facts, we have conducted the following work: 1) We have taken coroutines as the basic unit of kernel scheduling and implemented more precise scheduling to enhance the overall resource utilization.2) And we have designed an $O(1)$ complexity priority scheduling algorithm that cleverly unifies coroutine scheduling and process scheduling.3) We have used user-level interrupts to asynchronously transform system calls, improving the efficiency of waking up asynchronous coroutines. Finally, we have compared the efficiency of the thread model and the coroutine model on Qemu and FPGA, and found that coroutines have much lower overhead than threads in terms of context switching.


# 1. Introduction

As of 2022, Google's servers are handling 893[1] billion requests per day, with an average of 8 million requests per second, posing a great challenge for both hardware and software. Handling such a large number of asynchronous requests cannot be supported solely by threads. Therefore, mainstream operating systems have provided certain support for user-level asynchronous tasks. 

In the early days, Linux provided system calls such as [select and epoll](./bibtex_ref/epoll) to support user-level asynchronous I/O tasks by multiplexing multiple I/O operations on a single thread. The epoll operation uses a single thread to poll multiple listening ports, and when no event occurs, the polling operation will cause the polling thread to be block until an event arrives and wakes it up.  When an event occurs, the polling thread will copy the corresponding listening port from kernel space and send it to a separate thread for event processing. Windows I/O Completion Ports (IOCP) also provide a similar mechanism for I/O multiplexing. Unlike Linux, Windows IOCP calls the callback function in the completion thread for post-processing work after the completion of an I/O operation, making it a truly asynchronous I/O operation. Moreover, compilers and runtime libraries have built a set of independent scheduling systems in user space based on the asynchronous support provided by the operating system. In this system, the scheduling units are often referred to as coroutines and are only used by the user-space scheduler. Overall, although the kernel has provided some support for user-level asynchronous tasks, it can still only perceive a single listening thread working in the kernel and cannot truly perceive user-level asynchronous tasks, let alone finely allocate system resources according to the workload of each asynchronous task.

In addition to capturing execution errors in applications, the kernel also needs to handle high-privileged instructions such as device I/O operations. These events are not immediately triggered, and thus the kernel also requires a lightweight asynchronous task scheduling mechanism for performance optimization. [LXDs](./bibtex_ref/LXDs) has developed a lightweight asynchronous runtime environment in the kernel for cross-domain batch processing. This runtime environment allows lightweight processes to be created in the kernel that can execute tasks asynchronously, thereby improving system throughput and responsiveness. [Memif](./bibtex_ref/memif) is an operating system service for memory movement that provides a low-latency and low-overhead interface based on asynchronous and hardware-accelerated implementations. [Lee et al.](./bibtex_ref/lee) significantly improved application performance by reducing I/O latency through the introduction of an asynchronous I/O stack (AIOS) for the kernel. These approaches often propose an asynchronous task scheduling scheme that is independent of the kernel thread scheduler, which lacks generality and scalability and increases the complexity of the kernel.

Based on the above situation, we note that both kernel and user space require asynchronous task scheduling, and the scheduling characteristics are generally similar. Unfortunately, we have not found a unified and modular scheduling framework that can be provided to both user and kernel space. 

- 介绍当前主流内核对用户态的异步支持，指出主流内核对异步支持的一些缺陷：
	- 当前主流的宏内核中，协程仍然作为一种用户态管理的调度单位（例如tokio），无法被内核感知到，内核无法从系统层面对协程进行精细化管理。
	- 内核中缺乏轻量级的异步任务调度方案。内核往往也需要处理如设备读写等异步任务，近年的工作往往是提出一套独立于内核线程调度之外的单独的异步任务调度方案，首先是没有很好的通用性，其次也增加了内核的复杂度。
	- 在内核和用户态都需要异步调度、且调度特征大体相似的情况下，没有一个统一的、模块化的调度框架同时提供给用户程序和内核。

#  2. Relative Work

This chapter will provide a brief introduction to some of the existing technologies and methodologies used in this paper.

#### Async Support In Rust


#### User Interrupt Support


- Rust异步编程的机制介绍。
	- 有栈协程和无栈协程的对比。
- 用户态中断技术的介绍
	- 基本原理。
	- 与共享调度器的异步唤醒相结合。


# 3. Design and Implementation

## 3.1 Design
- 系统框架。
- 进程、线程、协程的概念重新定义。
- 调度器设计
	- 协程调度。
	- 进程、线程调度。
- 状态转换模型。
- 调度器提供的接口。
## 3.2  Implementation

- 局部优先级和全局优先级。
- 异步系统调用实现
	- 接口改造
	- 异步系统调用的唤醒机制实现（结合用户态中断）。
- 用户态中断唤醒的同步互斥的问题
- 兼容性实现
	- 用户态的代码入口为调度器初始化代码，为用户提供完全异步的环境。
	- 内核态的线程调度和协程调度的统一。
- 模块化调度器，用vdso在用户态和内核态复用了同一套调度代码。

# 4. Performance Evaluation
1. 用户态和内核态的优先级串口实验。
2. WebServer实验。
	1. 协程的切换开销远低于线程。
	2. 优先级在资源有限的情况下，保证某些任务能够高效完成。

# 5. Conclusion
- 总结本文工作，重申实验结论。
	- 将协程作为内核衡量调度的因素，提升系统资源的整体利用率。
	- 协程优先级。
	- 利用用户态中断对IO系统调用进行了异步化改造。
	- 实验结论。