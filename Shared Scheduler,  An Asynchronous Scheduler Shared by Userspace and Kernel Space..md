

## SharedScheduler: Coroutine scheduling framework across privilege levels

> SharedScheduler：跨特权级的协程调度框架

### Abstract

As a classical concurrency model, multi-threading technology has been widely supported by numerous operating systems and extensively applied in various application programs. However, as concurrency increases, the high system overhead and context-switching costs of multi-threading model have gradually become unacceptable. As a result, user-level threads have emerged, but they often only have been supported by user-level  and are not recognized by the operating system, which led to the inability of the kernel to  estimate the workload of coroutine tasks in the system accurately to perform more precise scheduling strategy to achieve higher system resource utilization. Based on the above situation, we propose the Shared Scheduler with the following characteristics: 1) It introduces the coroutine control block that allows both the kernel and applications to be aware of the coroutine's state, serving as the fundamental unit for kernel scheduling. 2) It introduces the concept of priorities within coroutines and designed a unified set of priority-based scheduling algorithms for both user-level and kernel-level coordination.  Finally, we analyzed the characteristics of the Shared Scheduler on QEMU and FPGA platforms, concluding that the coroutine scheduling algorithms has advantages in terms of switch overhead and granularity of resource utilization control.

> Abstract: 本文提出 SharedScheduler，一种跨越特权级的协程调度框架。我们将协程引入到操作系统和应用程序中，作为最小的任务单元，用于替换传统的多线程并发模型。通过给协程附着上优先级，SharedScheduler 能够利用优先级位图机制实现对协程的调度，并且让操作系统能够在一定程度上感知用户态协程，从而实现跨越特权级协调统一调度的目的。为了解决纯用户态协程在面对真正的并发时无力的挑战，我们在 SharedScheduler 中封装了对硬件线程的抽象，并且将系统调用改造成异步的形式，从而充分利用起多处理器系统的优势。最终，我们构建出一个特定的 web server 应用场景，在 FPGA 平台上对 SharedScheduler 进行了测试，结果证明它的确能够利用优先级实现对协程的精准控制，并且使用协程能够显著减小多线程并发模型带来的开销。



### 1. Introduction

In the early days, operating systems introduced the abstraction of processes to meet the concurrency and isolation requirements of multiprogramming. However, due to the large resource granularity of processes and the high cost of inter-process communication, operating systems proposed the abstraction of threads as the basic scheduling unit. Threads share the same address space, enabling efficient communication among them. With the rapid increase in concurrency, the use of threads as concurrency units has gradually become unacceptable in terms of resource utilization. As of 2022, Google's servers are [handling 893 billion requests per day](./bibtex_ref/google10search), with an average of 8 million requests per second, posing a great challenge for both hardware and software. Handling such a large number of asynchronous requests cannot be supported solely by threads. In addition, as resource-constrained embedded devices become [increasingly commonplace in various fields](./bibtex_ref/mahbub2020iot) such as agriculture, education, and healthcare, the abstraction of threads still appears somewhat bloated in such devices. In scenarios with high concurrency or resource constraints, the industry has provided some solutions in both operating systems and programming languages. 

Linux provided system calls such as [select and epoll](./bibtex_ref/epoll) to support user-level asynchronous I/O tasks by multiplexing multiple I/O operations on a single thread. The epoll operation uses a single thread to poll multiple listening ports, and when no event occurs, the polling operation will cause the polling thread to be block until an event arrives and wakes it up.  When an event occurs, the polling thread will copy the corresponding listening port from kernel space and send it to a separate thread for event processing. Windows [I/O Completion Ports (IOCP)](./bibtex_ref/IOCP) also provide a similar mechanism for I/O multiplexing. Unlike Linux, Windows IOCP calls the callback function in the completion thread for post-processing work after the completion of an I/O operation, making it a truly asynchronous I/O operation. Although I/O multiplexing technology can effectively reduce thread resource waste, from the kernel's perspective, the poll thread is just an ordinary thread participating in regular scheduling, and the kernel cannot perceive the asynchronous tasks aggregated in the poll thread. Furthermore, I/O multiplexing forces user-level applications to adopt the producer-consumer model for handling asynchronous tasks, reducing the flexibility of user-level operations. [Native AIO](./bibtex_ref/nativeAIO) is a set of asynchronous I/O interfaces supported by the kernel, which avoids frequent switching and data copying between user space and the kernel. However, because it requires kernel support, it can only be used on specific operating system architectures and has poor compatibility. IO_uring is a relatively recent technology that adopts an innovative asynchronous method, allowing for the direct submission of IO requests in user mode, thus eliminating the need for context switches between user and kernel spaces. Additionally, it utilizes shared memory between user and kernel modes to prevent memory copying, thereby enhancing IO processing efficiency and throughput. However, excessive design has led to an increase in kernel complexity and a greater difficulty in utilizing the interface. （这一段是介绍多线程模型与异步 I/O 结合的研究）

Moreover, compilers and runtime libraries have built a set of independent scheduling systems in user space based on the asynchronous support provided by the operating system. User-level thread such as goroutine,  is an independent asynchronous runtime environment built on top of an operating system, which has lower context switching overhead than kernel threads and less invasive impact on the code. It is common practice to create multiple user-level threads within a single kernel thread to enhance concurrency. [POSIX AIO](./bibtex_ref/posix-aio) is a set of asynchronous I/O interfaces implemented in user space through the POSIX thread interface, which is compatible with different architectures and operating systems that support the POSIX standard. Since the kernel is not aware of asynchronous tasks, there are significant overheads, including thread creation, scheduling, destruction, I/O buffer copying, and context switching cross domain. There has been considerable work on user-level threads and asynchronous runtimes in user mode. However, these implementations are built on top of the kernel, making it difficult for the kernel to perceive coroutines in user mode, consequently preventing the kernel from performing fine-grained resource scheduling. （这一段介绍纯用户态的线程或者协程模型）

In addition to capturing execution errors in applications, the kernel also needs to handle high-privileged instructions such as device I/O operations. These events are not immediately triggered, thus the kernel also requires a lightweight asynchronous task scheduling mechanism for performance optimization. [LXDs](./bibtex_ref/LXDs) has developed a lightweight asynchronous runtime environment in the kernel for cross-domain batch processing. This runtime environment allows lightweight cooperative threads to be created in the kernel that can execute tasks asynchronously, thereby improving system throughput. [Memif](./bibtex_ref/memif) is an operating system service for memory movement that provides a low-latency and low-overhead interface based on asynchronous and hardware-accelerated implementations. [Lee et al.](lee2019asynchronous,.md) significantly improved application performance by reducing I/O latency through the introduction of an asynchronous I/O stack (AIOS) for the kernel. [PM-AIO](./bibtex_ref/Pm-aio) indicates that the Native AIO path appears as a pseudo-asynchronous IO in the PM file system, and true asynchronous AIO is achieved by splitting IO requests into different sub-files. Due to the lack of coroutine support within the kernel, these approaches often propose asynchronous task scheduling schemes that are independent of the kernel thread scheduler, resulting in a lack of generality and scalability, as well as increased kernel complexity. （这一段介绍内核中的异步任务框架）


Based on the aforementioned discussion, we can summarize the following issues in the current state of asynchronous task scheduling in the industry:

1. The kernel provides basic abstractions such as processes and threads, but for high-concurrency and resource-limited scenarios, these abstractions may not be lightweight enough.
2. Lightweight runtimes provided in user mode, such as user-level threads, cannot be directly perceived and scheduled by the kernel, leading to the kernel's inability to precisely control resource allocation.
3. Some asynchronous tasks within the kernel itself (such as cross-domain communication in LXDs) are built as separate runtimes within the kernel, lacking a unified scheduling framework.

Therefore, based on the aforementioned issues, we propose our Shared Scheduler, which introduces stackless coroutines with priority into both the kernel and applications, serving as the kernel's fundamental scheduling unit. This provides a unified scheduling framework for all asynchronous tasks within the kernel. Additionally, it enables the kernel to perceive the priority of user coroutines, allowing for fine-grained scheduling of user coroutines and ensuring precise allocation of system resources.

> Introduction: 目前的 web server 具有不断增强并发性、可扩展性的需求。大规模的 web server 必须容纳数以万计同时存在的客户端连接，并且不能产生明显的性能下降。截至2022年，谷歌服务器每天处理8830亿次请求，平均每秒处理800万次请求。针对如此大规模的并发程序，多线程模型取得了一定程度上的成功，但随着需求逐步扩大，多线程模型的不合适性逐渐暴露出来。
>
> 1）线程作为底层硬件的抽象，是非常不确定的，适合于不确定的并发结构中（引用 The Problem with Threads），而在 web server 这种并发场景下，需要做的是监听收到的请求包，进行处理并返回结果给客户端，这种确定性的结构，使用多线性模型是非常不合适的。
>
> 2）多线程模型很难使用异步 I/O，尽管可以与操作系统底层的事件驱动模型进行结合，但会增加操作系统的复杂性。例如，Linux提供了 [select and epoll](./bibtex_ref/epoll) 等系统调用，通过在单个线程上复用多个I/O操作来支持用户级异步I/O任务。epoll 将多线程模型与事件驱动相结合，但仍需要操作单个线程来轮询多个侦听端口，当没有事件发生时，轮询操作将导致轮询线程被阻塞，直到事件到达并唤醒它。当事件发生时，轮询线程将从内核空间复制相应的侦听端口，并将其发送给单独的线程进行事件处理，这种做法迫使应用程序开发人员采用生产者-消费者模型进行事件分发。Windows 的 [I/O Completion Ports (IOCP)](./bibtex_ref/IOCP) 也提供了类似的I/O多路复用机制，但它更加接近事件驱动模型，在完成I/O操作后调用线程中的回调函数进行后处理工作，使其成为真正的异步 I/O 操作。[Native AIO](./bibtex_ref/nativeAIO) 是内核支持的一组异步 I/O 接口，避免了用户空间和内核之间频繁的切换和数据复制。但是，由于它需要内核支持，因此只能在特定的操作系统体系结构上使用，兼容性较差。而 io_uring 则采用了一种创新的异步方法，允许在用户模式下直接提交 IO 请求，从而消除了在用户和内核空间之间切换上下文的需要。此外，它利用用户模式和内核模式之间的共享内存来防止内存复制，从而提高IO处理效率和吞吐量。然而，过度的设计导致了内核复杂性的增加和使用接口的更大困难。除此之外，还有通过 POSIX 线程接口直接在用户空间实现的异步 I/O 接口 [POSIX AIO](./bibtex_ref/ POSIX - AIO)，它兼容支持 POSIX 标准的不同架构和操作系统。但由于操作系统不知道异步任务，因此有很大的开销，包括线程创建、调度、销毁、I/O缓冲区复制和跨域上下文切换。
>
> 3）线程需要占用的资源较多，而纯用户态线程在面对真正的并发时是无能为力的。内核支持的线程需要一套完整的硬件线程抽象（堆栈、通用寄存器、程序计数器等），因此不仅占用的资源较多，且其切换开销较大，在大规模并发时，会带来严重的性能下降。尽管用户态线程能够减少切换开销，增强灵活性，例如 goroutine，但通常是将多个用户态线程映射到一个内核线程上，因此操作系统很难感知用户态线程，不能执行细粒度的资源调度，面对真正的并发时无能为力。
>
> 在针对多线程模型不适用于大规模并发的 web server 场景的问题，已经展开了很多研究工作，但大部分仍然选择继续使用线程这个不轻量的抽象，没有从根本上解决问题。除了上述问题，在大规模并发的 web server 程序中还需要异步 I/O 机制的支持，这给操作系统带来了严峻的挑战。操作系统不仅需要给应用程序提供异步 I/O 支持，还需要给自身的一些异步任务构建出一套运行时。尽管已经有相关的研究展开，例如，[LXDs](./bibtex_ref/LXDs) 在内核中开发了一个轻量级的异步运行时环境，用于跨域批处理。这个运行时环境允许在内核中创建轻量级协作线程，这些线程可以异步执行任务，从而提高系统吞吐量；[Memif](./bibtex_ref/ Memif) 是一个用于内存移动的操作系统服务，它提供了一个基于异步和硬件加速实现的低延迟和低开销接口；[Lee等人]((lee2019asynchronous,.md))通过为内核引入异步 I/O 堆栈（AIOS）来减少 I/O 延迟，从而显著提高了应用程序性能；但这些方法通常独立于内核线程调度器之外，导致缺乏通用性和可伸缩性，并且增加了操作系统内核的复杂性。
>
> 在本文中，我们提出 SharedScheduler，一种跨越特权级的协程调度框架，用于解决上述的问题。与之前的工作相似，SharedScheduler 使用用户态协程来允许在单个硬件线程抽象上进行多任务并发。而 SharedScheduler 的独特之处在于给协程附着上优先级，并且将其引入到操作系统内，作为基本的任务单元，为操作系统中的所有异步任务提供协调统一的调度框架，对协程进行细粒度的调度，确保系统资源的精准分配。
>
> （需要标注线程指的是内核支持的线程，用户态线程则会显著指明为用户态线程。）

### 2. Background And Motivation

In order to enhance the performance of I/O-intensive applications, such as network applications and disk I/O applications, both the kernel and user space provide certain levels of asynchronous support. This chapter primarily focuses on widely used user-space coroutine technology and kernel-level I/O multiplexing technology in the industry.

#### 2.1 Coroutine

Coroutine is a lightweight concurrency programming technique that enables cooperative scheduling of multiple execution flows within a single kernel thread. Compared to traditional kernel threads or processes, coroutines have lower resource overhead and higher execution efficiency. Coroutines can be seen as user-level threads that are actively controlled by programmers for scheduling and context switching. Modern programming languages such as[ C++20](./bibtex_ref/cpp-coroutine), [Go](./bibtex_ref/goroutine), [Rust](./bibtex_ref/rust-async), [Python](./bibtex_ref/python-coroutine), [Kotlin](./bibtex_ref/kotlin-coroutine), etc., offer varying degrees of support for coroutines. In order to strike a balance between usability, safety, and performance, we compared the support for coroutines in Rust and Go programming languages within the kernel.

[Goroutine](./bibtex_ref/goroutine) is a coroutine implementation in the Go programming language, based on the stackful coroutine model. Goroutine simplifies and enhances concurrent programming, allowing for a large number of concurrent executions within a single kernel thread. In the Go language, Goroutines are created using the "go" keyword followed by a function call. This function call runs concurrently with other Goroutines in the same address space. Goroutines have their own stack space, which is dynamically allocated and managed by the Go runtime. This stack space enables Goroutines to have independent execution contexts, including local variables and function calls.

Coroutines in the Rust language are implemented through the async/await syntax, the async keyword, and the corresponding runtime library. Compared to goroutines, Rust coroutines are implemented as stackless coroutines, which do not require pre-allocated fixed-sized stack space. Instead, the stack space for coroutines is dynamically allocated and deallocated as needed. This allows coroutines to be created and destroyed very lightweightly and efficiently. Furthermore, thanks to the rigorous checking mechanisms of the Rust compiler, Rust coroutines also possess significant advantages in terms of memory safety. These are two reasons why we prefer Rust coroutines.

However, we have noticed that at the application layer, coroutine implementations cannot be directly recognized by the kernel. Specifically, the kernel can only perceive the processes and threads of user programs. In an extreme scenario, a process with thousands of coroutine tasks may appear no different to the kernel than a thread with just a single coroutine task. In order to enable the kernel to make appropriate resource allocations based on the actual workload of tasks, it becomes necessary to make the kernel aware of the presence of user coroutines.

#### 2.2 Asynchronous tasks in kernel

In the kernel of an operating system, asynchronous tasks refer to tasks that can be executed in the background without blocking the main thread or other tasks. Asynchronous tasks are typically executed in an event-driven manner, where the kernel initiates corresponding asynchronous tasks to handle specific events when they occur. The kernel only provides an abstraction for threads in its design, but it is impractical to allocate a separate kernel thread for each asynchronous task. Some efforts have been made to handle asynchronous tasks in the kernel by building a lightweight thread runtime specifically for that purpose, such as cross-domain communication in LXD. However, this approach fails to provide a unified scheduling mechanism for regular threads and lightweight threads within the kernel, leading to increased complexity in kernel scheduling.

Another widely used technique is I/O multiplexing, which allows a thread to monitor multiple IO events, such as read and write operations on network sockets or the readiness state of file descriptors, without having to create separate threads or processes for each IO operation. However, to ensure prompt event responsiveness, the event loop thread often refrains from engaging in any additional time-consuming operations. Instead, it typically dispatches events to other threads for processing. This practice compels application developers to adopt the producer-consumer model for event distribution.

We have designed a simple network scenario where multiple clients need to send a local matrix to a server for time-consuming computations, and then receive the computed result back from the server. One widely adopted solution in the industry involves the use of IO multiplexing techniques on the server-side. This solution utilizes a poll thread to monitor the sockets of all connected clients. Upon receiving a request message, the poll thread directly sends it to a message queue. Subsequently, another processing thread continuously retrieves requests from the message queue, handles them, and returns the corresponding responses. This architecture represents a classic example of the producer-consumer model. The data race issue arising from the producer-consumer model often poses certain demands on the proficiency of application programmers.

We have observed that due to the coarse granularity of kernel thread resources, IO multiplexing chooses to aggregate multiple IO listening events into a single thread, which inevitably leads to event dispatching. To fundamentally address this issue, we introduce coroutines with finer resource granularity into the kernel, making them the smallest units for listening to IO ports and participating in unified kernel scheduling. Kernel coroutines correspond one-to-one with user coroutines, thereby eliminating the necessity for event dispatching at its core.

> Background And Motivation：
>
> 近年来，协同程序引起了广泛的关注，例如 DepFast 在分布式仲裁系统中使用协程；Capriccio 使用相互协作的用户态线程来实现可扩展的大规模 web server。根据前人的研究，我们认为协同程序在构建大规模并发程序的场景下是大有作为的。
>
> 协同程序是一种轻量级的并发编程技术，支持在单个内核线程上协作调度多个执行流。与传统的内核线程或进程相比，协同程序具有更低的资源开销和更高的执行效率。现代的编程语言，如[c++ 20](./bibtex_ref/ pcp -coroutine)、[Go](./bibtex_ref/goroutine)、[Rust](./bibtex_ref/ Rust -async)、[Python](./bibtex_ref/ Python -coroutine)、[Kotlin](./bibtex_ref/ Kotlin -coroutine)等，都为协同程序提供了不同程度的支持，根据协同程序的实现方式，可以划分为以下两类：
>
> 1）Stackful：一类为用户态线程，其中以 Go 语言提供的 [Goroutine](./bibtex_ref/ Goroutine) 为代表。Goroutine 是 Go 编程语言中的协同程序实现，它简化并增强了并发编程，允许在单个内核线程内进行大量并发执行。在 Go 语言中，使用 “Go” 关键字后跟一个函数调用来创建 Goroutine。此函数调用与同一地址空间中的其他 Goroutine 并发运行。Goroutine 有自己的运行栈空间，由 Go 语言内集成的运行时动态分配和管理，这个栈空间能够用于保存局部变量和函数调用关系。因此，这类用户态线程相比于内核线程，减少了寄存器切换时的开销，但效果有限。
>
> 2）Stackless：另一类则是以 Rust 语言为代表的无栈协程。Rust 语言支持的协程是通过 async/await 语法和相应的运行时库实现的。与用户态线程相比，Rust 协程是作为无栈的，它不需要预先分配固定大小的栈空间。相反，协程的栈空间是根据需求进行动态分配和释放的。这使得协程的创建和销毁非常轻巧和高效。
>
> 综合上述分析，我们选择了使用无栈协程来替换传统的多线程模型，将其应用在大规模并发的 web server 场景中，并且由于 Rust 语言编译器的严格检查机制以及内存安全方面的显著优势，我们选择了 Rust 协程。随着对 Rust 协程的进一步了解，我们逐渐认识到协程与异步 I/O 机制之间的紧密关系（加引用），并且 Rust 提供的高级抽象使得系统开发人员能够灵活的定义协程，我们可以在内核中引入与用户态协程一一对应的内核协程，用于处理各种各样的异步任务，从而消除内核底层事件驱动的必要性。这给在操作系统中定义一套统一的异步任务调度机制提供了契机。
>
> 动机：我们针对大规模并发的 web server 场景下的研究，以及学术界和工业界对协程的关注促使我们开始思考重新并发模型和异步框架，寻求能够满足更大规模、更高性能需求的解决方案。为此，我们提出了一个跨越特权级的协程调度框架，让操作系统内核中的异步 I/O 任务与用户态协程的调度能够协调统一，提供一套统一的异步 I/O 框架，同时满足高并发的需求。

# 3. Design

In this section, we will introduce a kernel design scheme suitable for highly concurrent, asynchronous scenarios. It builds and improves on the traditional multi-process, multi-threaded model by replacing the task unit with a more lightweight coroutine, and bring it into the kernel to replace the responsibilities of the original thread. The design has the following four key enabling techniques, i.e., develping a set of data structure to control the coroutines  (Section 3.1), weaking the concept of thread and constructing  a coroutine state transition model (Section 3.2), using kernel coroutines (section 3.3), harmonizing task scheduling between the kernel and user processes by share schedulers (section 3.3).  Figure 1 shows the overall architecture of our design.

<div>
    <center>
    <img src="./Article/assets/archtecture.png"
         style="zoom:50%"/>
    <br>		<!--换行-->
    Figure 1, system architecture overview.
    </center>
</div>


==这张图里面，可以把全局位图和进程的关系，给重新描述一下。关于内核里的进程的图示，这部分可以画的更好，并且需要体现统一调度。==

### 3.1 Coroutine Runtime

The Rust language provides two very high-level abstractions, ***Future*** and ***Wake***, to support the coroutine mechanism without limiting how the underlying runtime can be implemented. Therefore, we can take advantage of this decoupling property to customize a runtime that can be adapted in both kernel and user process. The coroutine runtime mainly consists of the following components: 1) Coroutine control block; 2) Executor.

#### 3.1.1 Coroutine Control Block

The Rust language provides the async and await keywords to make creating coroutines very easy. However, this convenience means that the execution of the coroutine is obscure and opaque, and the control of the coroutine cannot be accurately completed. Therefore, on the basis of Future and Waker abstractions provided by Rust language, we add additional fields to form a coroutine control block, so as to achieve accurate control of coroutines.

```rust
pub struct Coroutine{
    /// Immutable fields
    pub cid: CoroutineId,
    pub kind: CoroutineKind,
    /// Mutable fields
    pub prio: usize,
    pub future: Pin<Box<dyn Future<Output=()> + 'static + Send + Sync>>, 
    pub waker: Arc<Waker>,
}
```

Coroutine control block structure. Coroutines are similar to processes and threads. How to promote the execution of coroutines and how to switch and save the context of coroutines is the most important problem. Fortunately, Rust already provides two relatively well-developed abstractions, Future and Wake. The poll function required by the Future abstraction is used to drive coroutine execution, while the Wake abstraction is closely related to save and switch the context of coroutine . The execution and context switching of the coroutine are both done by the compiler to help us and are opaque. Therefore, the future and waker must be described in the coroutine control block. However, these two fields alone cannot achieve the purpose of accurate control. In the coroutine control block, three additional fields are added, among which id is used to identify the coroutine control block. The type field is used to indicate the task type corresponding to the coroutine. According to the task type of the coroutine, different processing is carried out. The prio field represents the priority order of tasks, which is the basis for scheduling order. These extra fields will be used to achieve accurate control of coroutines in the kernel, making the compiler work closely with the operating system kernel. Note that there is no coroutine state field in the coroutine control block, the state of the coroutine is implicitly described by the queue in which it is located. More detailed state transitions are described in the section 3.2.

#### 3.1.2 Executor

In addition to controlling individual coroutines, an Executor structure is needed to manage all coroutines in a process. 

**Coroutine queue**: The Executor maintains several priority queues that the coroutine will be stored in the queue corresponding to its priority, which guarantees that the coroutine with highest priority can execute firstly each time. In addition, the Executor maintains a blocked queue for blocked coroutines.

**Priority**: In addition to the priority queue, the Executor needs to maintain a priority bitmap to indicate whether the corresponding priority exists as a coroutine, but this increases the complexity. Actually, the kernel does not need to be aware of all the coroutines within the user process address space, only the coroutine with the highest priority. Therefore, the Executor needs to maintain a priority that represents the highest priority among all coroutines, as well as the priority of the process. The priority field will be updated when the coroutine is added, awakened, or executed.

**Synchronization and mutual exclusion**：With the two simple mechanisms described above, Executor meets the basic requirements of managing and controlling coroutines. In cases where the number of coroutines is small, it is perfectly sufficient to allocate a single CPU to the process, but when the number of coroutines increases, multiple cpus have to be allocated to the process to accommodate the increased workload, and the current Executor actually manages the coroutine as a global queue, which creates the problem of synchronous mutual exclusion. In addition, there is also the problem of synchronous mutual exclusion when a blocking coroutine is awakened. Therefore, all data structures in the Executor are maintained through atomic operations. 

**CPU’s affinity**: When a process is assigned to multiple cpus, coroutines may move between multiple cpus, but this does not affect the CPU's affinity for coroutines because they all run on the same address space.



### 3.2 Coroutine State Model

The importation of coroutines into multi-process and multi-thread models will inevitably bring some new changes, and these concepts need to be analyzed. If the kernel is regarded as a special process, and under the full kernel isolation mechanism, entering the kernel and returning the user process  both need to switch the address space, so the role of the process is very clear, in order to ensure the address space isolation. As for the thread, we have greatly weakened its role, in the traditional kernel, the thread will be bound to a specific task, but after the importation of coroutines, the thread is not bound to a specific task, only to provide a running stack for the coroutine. So instead of building a thread state transition model, we only need to build a coroutine state transition model. Similar to the five-state transition model of threads, coroutines should also have five states: create, ready, running, blocked, and exit, but there are some differences. Since the coroutine provided by Rust language is stackless, in general, the coroutine only has a stack when it is running, but because the kernel provides preemptive scheduling, a coroutine may be interrupted by interrupt or exception when it is executing. At this point, the coroutine still occupies a stack, but it is no longer running on the CPU. We define it as the running suspended state. According to the causes, it can be divided into the running interrupted state and the running exception state. The coroutine state transition model is shown in the figure 3.

- Once a coroutine is created, it goes into a ready state until it is scheduled and thus into a running state.
- For coroutines in the running state, possible state transitions can be divided into two categories. On the one hand, during the running process, it may wait for some event to enter the blocked state, or detect other coroutines with higher priority (including those in other processes) and actively give up to enter the ready state. This state transition will not occupy the running stack; On the other hand, if an interrupt or exception occurs while it is running, the CPU will be preempted, and the current coroutine will enter the running suspended state. At this time, the coroutine will still occupy the running stack. In addition, a running coroutine will enter the exit state waiting to reclaim resources when the task is finished.
- When the coroutine is in the blocked state, it must wait for an event to wake itself up and thus enter the ready state. However, when the coroutine is in the running suspended state, it does not need to go through the ready state transformation, only need to wait for the time, can directly enter the running state.

<div>
    <center>
    <img src="./Article/assets/cstate.png"
         style="zoom:100%"/>
    <br>		<!--换行-->
    Figure 3, Coroutine state transition model. 	<!--标题-->
    </center>
</div>


### 3.3 Kernel Coroutine

The current mainstream practice is to use coroutines in user mode, and our design innovates on this point by importing coroutines into the kernel as well, and all tasks in the kernel are described in coroutines. The main functions provided by the kernel are process management, memory management, file system, device management, network management and so on. For normal synchronous tasks, the use of coroutines will not increase its overhead, and for the kernel to deal with external events, IO and other asynchronous tasks, the use of coroutines can better play the advantages of collaborative scheduling. However, there is a special task in the kernel, switching address spaces and running stacks, which consists of a piece of assembly code that is only called when the process is scheduled. Once this task is described in coroutine (switching coroutine, sc), new problems arise. First of all, it's a special coroutine that never ends. Second, its priority should be dynamic, aligned with the highest priority of all user processes. The sc will execute when there is no other coroutine in the kernel or the other coroutine has a lower priority, then the system will switch to the process address space with the highest priority, and switch the running stack. When there are other coroutines with higher priority in the kernel, the other coroutines will be executed first. Therefore, it is feasible to import coroutines into the kernel.



==解释内核中的每段代码属于什么对象==


### 3.4 Shared Scheduler

In addition to importing coroutines into the kernel, what we also need to do is to make the kernel aware of coroutines in user process, so that the kernel and user process task scheduling will be coordinated. This is exactly what the shared scheduler is designed for. It ensures that task scheduling can be coordinated and unified from two levels. On the one hand, the shared scheduler provides a runtime (Executor) for the kernel or process to ensure that the local scheduling of intra-process coroutines can be ordered. The Executor maintains a local priority bitmap and sevaral task queues corresponding to different priorities that hold the id field in the coroutine control block. Each bit in the bitmap indicates whether there is a coroutine with a corresponding priority. Local priority bitmaps are maintained according to the priority field in the coroutine control block when coroutines are created, scheduled, and deleted. When scheduling, the shared scheduler only needs to remove the coroutine id from the task queue with the highest priority, so that the kernel or process can always select the coroutine with the highest priority during each scheduling.

On the other hand, the shared scheduler need to coordinat the global scheduling between the kernel and other user processes. Because all task in the kernel or user process exist in the form of coroutines, it is natural to use the highest priority of all coroutines in the kernel or process to represent the priority of the owning process, so as to schedule according to the priority of the process. Therefore, it is also necessary to maintain a global priority bitmap that the kernel has readable and writable permissions, and the global priority bitmap is maintained by the kernel actively scanning the local priority bitmap in all process executors each time system enters the kernel. Other user processes only have readable permissions, once they detect the existence of higher priority coroutines in the kernel or other processes during running, they will take the initiative to yield CPU, so as to achieve mutual coordination.

In summary, the shared scheduler enables the kernel and processes to work in a coordinated and orderly manner. The main logic of a shared scheduler can be represented by figure 4.



<div>
    <center>
    <img src="./Article/assets/flow.png"
         style="zoom:100%"/>
    <br>		<!--换行-->
    Figure 4, Shared scheduler's Control logic. 	<!--标题-->
    </center>
</div>


> Design：

它们基于一个非常简单的原则:确定性的目的应该用确定性的手段来实现。不确定性应该在需要的地方谨慎地引入，并且应该在程序中明确。

协程之间的确定性，不确定性在 await 处，显示的，谨慎的引入。



用户态线程 == 协程

事件驱动机制 == 用户态中断

协程与多处理器之间的问题 == 共享调度器






# 4. Implementation（这一部分的 内容需要大改）

We implement the above design scheme on the basis of rCore, and build a set of asynchronous software ecology, so that the kernel can adapt to high concurrency, asynchronous scenarios. In this section, we will show the implementation details.

### 4.1 APIs

We implement the shared scheduler mentioned in Section 3.3 as a kernel loadable module and provide the shared scheduler to user processes in the form of a vDSO, which reduces the overhead in the form of a common library and does not impose additional burden on the application developer. The API exposed is shown in the table 1.

| Function | Description                                  |
| -------- | -------------------------------------------- |
| spawn    | Create a new coroutine.                      |
| get_cid  | Get the current coroutine id.                |
| wake     | Wake up a specific coroutine.                |
| reprio   | Adjust the priority of a specific coroutine. |

### 4.2 Completely asynchronous scheduling environment

We make compatibility adjustments to the Unix-like runtime environment for the user process, which does not execute the main function immediately after it is initialized. The main function is encapsulated into an asynchronous coroutine (equivalent to synchronous tasks that cannot be waited), called the main coroutine, and adds it to the ready queue for unified scheduling, which means that all tasks in the user process are in an asynchronous execution environment.

### 4.3 Asynchronous IO system calls

Synchronous IO system calls, such as "read", will block the entire thread. In a fully asynchronous coroutine programming environment, it is necessary to transform system calls into asynchronous operations to ensure that they only block the current coroutine at most. The support for asynchronous IO system calls mainly involves two parts: user space and kernel space.

#### 4.3.1 User Space Modification

The modification of the user space system call interface to support asynchronous calls needs to consider both functional differences and formal consistency. There should be an effort to minimize the differences from synchronous system calls. Additionally, automation should be considered throughout the modification.

To enable system calls to support asynchronous features, an `AsyncCall` auxiliary data structure needs to be added, which shoule implement the Future trait. After completing this work, the `await` keyword can be used when calling the asynchronous system calls.

The formal differences should be minimized as much as possible. We use Rust language procedural macros to generate both synchronous and asynchronous system calls. Finally, synchronous and asynchronous system calls achieve a high degree of consistency in the form, with the only difference being the parameters. The format is shown in the table below.

```rust
#[async_fn(true)] 
pub fn read(fd: usize, buffer: &mut [u8], key: usize, cid: usize) -> isize {
	sys_read(fd, buffer.as_mut_ptr() as usize, buffer.len(), key, cid) 
}

#[async_fn]
pub fn write(fd: usize, buffer: &[u8], key: usize, cid: usize) -> isize { 
	sys_write(fd, buffer.as_ptr() as usize, buffer.len(), key, cid) 
}

read!(socked_fd, buffer, key, current_cid); // async call
read!(socked_fd, buffer); // sync call
```

#### 4.3.2 Kernel Space Modification

In addition to ensuring formal consistency in the user-level system call interface, we also aim for consistency in the kernel system call processing interface. Ultimately, the kernel determines whether to execute synchronous or asynchronous processing logic based on the system call parameters. In the case of asynchronous processing, the kernel uses some method to immediately return the task to user space without waiting for the corresponding processing flow to complete synchronously. Once the kernel completes the corresponding asynchronous processing, it wakes up the corresponding user-level coroutine.

For instance, the following diagram illustrates the entire workflow of an asynchronous system call for socket read operation. After entering the kernel, the operations that were originally done synchronously by kernel will be encapsulated into a kernel coroutine, which is then added to the kernel Executor. Then it immediately returns to user space and generates a future to wait for the waking up of the user coroutine that executes the asynchronous system call. At this time, the shared-scheduler will switches to execute the next user coroutine. After the asynchronous system call returns to user space, the kernel coroutine which encapsulates related operations is not executed. The kernel coroutine waits for the network driver to notify the kernel after the data is ready, and then the kernel coroutine is awakened to execute the corresponding operations. Once the kernel finishes the workflow (in this case, copying data to the user space buffer), it generates a user space interrupt, passing the ID of the corresponding user coroutine to be awakened. The user space interrupt handler then wakes up the corresponding coroutine.

![](./Article/assets/Async_Syscall.png)


# 5. Performance Evaluation



加入一些现实的背景问题，可以在实验部分进行详细描述，例如在线实时的深度学习，接收到发来的数据，进行矩阵运算，再返回原来的处理值。

 webserver 面临的问题，深度学习推荐系统需要实现低延迟的模型更新，从而让新的内容和用户及时地在推荐服务中展示。然而，现有的深度学习推荐系统无法满足这种需求。它们往往以离线的方式训练和验证模型，之后将模型从单个训练集群中广播给部署在全球推理集群中的模型副本。这种做法会产生分钟甚至小时级别的模型更新延迟，从而对推荐服务的质量（Service-Level Objectives, SLOs）产生负面影响。



详细描述设置，线程创建于销毁不会带来影响，纯粹比切换的开销。



To demonstrate the lower switching overhead of coroutine programming model compared to thread programming model, we constructed two different TcpServer models using coroutine and thread respectively to test the server's throughput, message latency, and latency jitter.

In addition, we will demonstrate the significant role of priority in ensuring the real-time performance of certain specific tasks under limited resources by analyzing the impact of coroutine priority on task throughput, message latency, and latency jitter in the TcpServer experiment.

We implemented the shared-scheduler based on rCore, which is a small operating system almost entirely written in Rust, characterized by its compactness and efficiency. It can also fully leverage Rust's support for asynchronous programming to quickly implement the shared-scheduler.

The Msg Send stage in the client periodically sends a certain length of data to the server, while the Msg Recv in the client receives the server's response, calculates the response latency, and waits for the timer to expire before sending the next request. Each connection in the server consists of three components:

- **Msg Recv**, which receives requests from the client and stores them in the request queue.
- **Req Handler**, which takes messages from the request message queue, performs matrix operations, and sends the results to the response message queue.
- **Msg Send**, which takes responses from the response message queue and send them to the client.

These three components transfer data through the shared message buffers.

## 5.1 Coroutine programming model vs. thread programming model

To evaluate the advantages and disadvantages of the coroutine and thread programming models, as well as the switching overhead between them, we implemented the three components of the Server Process using the thread model and the coroutine model respectively. We represent the test results for processing 1 × 1 matrix requests in the thread model as Thread-1, and the test results for processing 20 × 20 matrix requests in the coroutine model as Coroutine-20. Similarly, the other results are represented accordingly. The experiments were conducted on 4 physical CPUs, with the server allocating 4 virtual CPUs. The timeout period set by the client's timer is 100ms.

The test results for message latency are shown in the following figure. As can be seen from the figure, the thread model has similar or even slightly lower message latency than the coroutine model when the number of connections is small. This is because when the number of connections is small, the kernel can directly schedule threads to execute tasks, while the coroutine model adds an extra layer of synchronization and mutual exclusion operations in the scheduler, resulting in slightly higher latency. As the number of connections increases, the delay of the thread model rapidly increases and is much higher than that of the coroutine model. This is because most coroutine switches do not need to trap into the kernel, only switching the function stack, resulting in much smaller switching overhead than threads. Comparing different matrix request sizes under the same model, it is found that the larger the matrix size, the higher the latency, which is due to the larger overhead of message sending and receiving and message processing for larger matrix requests, leading to an expected increase in latency.

![](./Article/assets/compare_thread_coroutine.png)

这里的图可以画条形图，对比会比较好一点

The figure also shows the test results of the total throughput for different matrix request sizes under different models. It can be seen that the total throughput of the server under the coroutine model increases linearly with the increase of the number of connections, even when the matrix request size increases. Since the load has not reached the peak (the client sends a request every 100ms, and the highest latency shown in the figure is only 10ms), the throughput depends on the number of connections and the client's request frequency. For the server under the thread model, it can keep up with the coroutine model when the number of connections is small, but as the number of connections increases, the switching overhead increases rapidly, leading to a slowing down of the total throughput increase trend. As for Thread-20, the load almost reaches its peak when the number of connections is around 64.

## 5.2 Priority-controlled resource allocation

In computer systems, both CPU and IO resources are always limited. Under such resource constraints, we can prioritize certain services by setting their priority levels. In the context of a TcpServer, we can set the priority levels of each connection in a hierarchical manner to ensure lower latency and reduced latency jitter for certain connections.

Our experiments were conducted on four physical CPUs. The clients sent request messages with a matrix size of 20x20 at a period of 50ms. The server was implemented using coroutines. We established 128 connections between the clients and server, divided equally among 8 priority levels, and tested the performance of the connections with different priority levels under different numbers of virtual CPU.

The test results are shown in the figure below, where "x-core" in the legend represents the number of virtual CPU cores allocated to the server. The results indicate that under resource constraints, only connections with higher priority levels (lower priority numbers) are able to achieve higher throughput and lower request latency. With the increase in resource quantity, the system is able to ensure that connections with lower priority levels also achieve higher throughput and lower latency, while still adhering to the requirement that the highest priority level has the highest throughput and lowest latency. Furthermore, we also observed that with the increase in virtual cores, there was a slight performance degradation for high-priority connections. This is due to the increased synchronization and mutual exclusion among poll threads in the scheduler caused by the increase in virtual cores. In the future, this issue can be alleviated by introducing multi-level ready queues.

![](./Article/assets/connect_with_prio.png)

We further analyzed the distribution of message latency for each priority level, as shown in the figure below. This largely conforms to the characteristics of prioritizing high-priority connections in request handling.

![](./Article/assets/connect_with_prio_delay_distribution.png)


# 6. Conclusion

In this paper, we propose a general and user/kernel-space shared asynchronous scheduling framework called the shared scheduler. We introduce the concept of coroutine into the kernel as a scheduling unit, reducing context switching overhead and improving system resource utilization. And we have designed an $O(1)$ complexity priority scheduling algorithm based on the priority of each coroutine. Finally, we implement asynchronous system calls using user-space interrupts to reduce the overhead of kernel-space context switching. In the scenario of TcpServer, the server implemented by the shared scheduler exhibits lower context switching overhead and higher resource utilization.

