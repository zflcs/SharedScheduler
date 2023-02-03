
中心论点：对进程、线程、协程的概念进行了新的尝试，并在这个基础上实现了共享调度器，给内核和用户程序提供了协程的异步运行时。


# SharedScheduler

### 论文大纲

### Abstract

简要描述全文的要点

### 1. Background and Motivation（先不考虑）

#### 1.1 高并发场景、嵌入式等受限制的设备上异步编程，使用无栈协程会更好

#### 1.2 Rust 只提供基本的 trait，不提供 runtime，而社区开发的第三方 runtime 多是基于 std 环境下，能在内核环境下运行的较少

#### 1.3 内核和用户程序进行异步编程都需要 runtime，因此有必要考虑到代码的重用性，因此通过 VDSO 的形式在内核和用户程序之间共享同一份代码

#### 1.4 rust async/await 模式

1. ##### 异步编程的发展趋势，在 设计文档里面有大致的趋势，之后再补充文献

#### 1.5 用户态中断

1. ##### x86 的用户态中断
2. ##### rCore-N

#### 1.6 rCore 多核

1. ##### 内核线程多核并行

### 2. 引入了协程机制带来的变化

> 本文的主要贡献之一是在引入了协程的概念之后，尝试对进程、线程等概念进行不同的解读。
> 
> 在最开始只有进程的概念时，进程既需要负责地址空间隔离，又需要保存在 CPU 上运行代码的寄存器信息。在出现多线程模型之后，进程负责地址空间隔离，线程则保存上下文信息。
>
> 提到线程模型，这里需要对内核支持的线程和用户支持的线程两种模型进行说明。传统的内核线程和用户线程没有关联，内核线程有内核提供一组接口供用户程序使用，由内核进行调度管理，某个内核线程阻塞时，其他线程不会受到影响。用户线程则是由用户库提供接口，由用户库提供调度管理，内核并不感知，因此，当一个用户线程阻塞在内核时，其他的用户线程均会被阻塞。因此，内核线程可以很好的支持抢占式多任务，而用户线程则比较适合协作式多任务。
> 
> 在没有协程的概念出现时，为了实现抢占式多任务系统和协作式多任务系统，如果仅仅依靠内核线程进行协作，从一个线程切换到另一个线程，需要陷入内核，这种开销很大，因此可以结合用户线程，协作式的任务由用户线程来完成，用户线程之间的切换不需要陷入内核，开销较小。
> 
> 协程的概念出现之后，实现协作式多任务系统的方式简单了，用协程来描述任务，任务切换时，和用户线程相似，不需要陷入内核，并且 Rust 提供的协程属于是无栈协程，不需要切换栈。因此，只需要将内核线程和协程这两个概念结合起来即可实现一个抢占式+协作式的多任务系统模型。
> 
> 新增了协程概念之后，尽管进程、线程的数据结构与多线程模型下没有区别，但是理解的方式不同了，线程不再与特定的某个任务（函数）进行绑定，而是被视为分配给某个进程的虚拟 CPU，负责调度协程，提供给协程代码运行所需要的栈。
>
> 协程则是作为任务的最小单位，一个协程在栈上运行完毕或者阻塞后，其在栈上的信息会被换出，供下一个协程执行。

![](./Article/assets/relation.excalidraw.png)

> 引入了协程的概念之后，任务的信息被描述在协程控制块中，并处于就绪队列中，在 CPU 开始执行某个任务之前，需要完成两个调度：（1）一级调度，选出某个进程中的某个线程；（2）在选出的进程中选出某个任务。
> 
> （1）一级调度：一般来说，进程需要调度，线程也需要进行调度。进程调度会切换地址空间，而线程调度则会切换上下文等信息，包括栈。我们将这两者的调度合并到了一起，进程控制块中的 prio 字段表示进程的优先级，作为进程调度的依据，选出最高优先级的进程。选定了某个进程之后，还需要选出目标进程内的某个线程，传统的多线程模型下，进程内的线程绑定了某个特定的任务（函数），这个任务也存在优先级，因此在这个阶段需要进行一次调度。但是，基于上述对线程新的理解，线程被认为是虚拟的 CPU，用于调度协程，并不与某个具体的任务进行绑定，因此线程控制块中不需要再保存优先级字段，所有的线程都是等价的，因此，这里不需要额外进行调度，从就绪队列中找到属于目标进程的位置最靠前的线程即可。因此，我们将这两种调度合并在一起，称之为一级调度。在初始化进程时，将进程的优先级设置为默认优先级（最高优先级），通过这种方式保证了新创建的进程的公平性，不会出现饥饿的情况，一旦进程开始运行，其优先级会动态的变化，这种变化将会在下文进行介绍。
> 
> （2）二级调度：协程作为任务的最小单元，每个协程都应该有各自的优先级，保存在协程控制块的 prio 字段中，我们采用了优先级位图来进行调度，位图中的一个 bit 对应着一个优先级队列，1 表示这个优先级的队列中存在待执行的协程，0 表示进程内不存着这个优先级的协程。对于协程的调度，每次取出优先级最高的协程运行，在每次调度之后，会更新优先级位图，使得其与进程内的协程的优先级始终保持一致，上文提到的进程优先级实际上是进程内所有协程的优先级的最高者，其动态变化与协程的调度相关。
> 
> 总结：引入了协程之后，仍然需要利用原来的进程、线程的数据结构，但是任务单元从线程转换到协程，这需要对线程进行不同的解读，并且在调度上也存在着不同。

### 3. 完全异步的场景下，控制流的变化

> 本项目的主要贡献除了对于进程、线程、协程的概念进行新的探讨，还基于 rCore-N 实现了一个简单的完全异步的模型，并对部分系统调用进行了改造。
>
> 上述的协程调度是利用优先级位图来进行，同时，rust 协程还要求手动提供一个异步运行时，因此，我们讲这两个机制融合到一起，形成了共享调度器。在完成内核其他模块的初始化之后，我们开始将共享调度器加载到内核之中，并建立地址映射关系，使得内核可以访问执行共享调度器的代码。当需要创建用户进程执行时，在解析 elf 建立地址空间时，我们会将共享调度器映射到进程的地址空间中，使得进程同样可以访问执行共享调度器代码，通过这种方式使得内核和所有的进程共享同一份代码。
> 
> 整体的流程图如下。内核根据进程的 elf 格式文件，解析并创建地址空间，将共享调度器地址映射加载到进程地址空间之后，紧接着我们会创建一个线程控制块，线程控制块中的上下文会被初始化（sp 寄存器指向事先准备好的一个空栈的栈顶，pc 寄存器被设置为共享调度器的入口）。当内核调度到这个线程时，CPU 控制权会转到用户进程地址空间里共享调度器的用户程序入口函数，完成用户进程的用户态的初始化工作之后，控制权会转移到 poll_future 函数中，这个函数的主要功能是不断从 Executor 中取出优先级最高的协程执行，这时控制权在 poll_future 函数和用户写的协程代码之间转移，这种控制流来回切换所需要保存的上下文仅仅是协程的上下文，因此其范围很小，不需要切换栈。在所有的协程运行结束之后，这也就意味着所有的任务已经完成，这时需要回收掉对应的进程、线程。
> 
> 上面描述的是不被抢占的情况下的控制流转移过程。但是，既然我们提到了是完全异步的场景，那么在任意的时刻，都有可能发生中断、异常或者系统调用，控制流就会发生转移，这些转移都需要经过内核的处理，再转移给同一进程中的其他线程或者其他进程中的线程。

#### 3.1 同一进程内线程之间控制流的转移

> 根据当前线程控制流和目标线程控制流所处的时刻，我们将其分为 3 种情况：（1）处于执行到某个协程的中间时刻；（2）处于 poll_future 调度函数阶段，已经调度到某个协程，但尚未执行；（3）处于 poll_future 调度函数阶段，
> 
> （1）在任意时刻发生了中断、异常，转移到同一个进程中的其他线程。这里的任意时刻还可以继续划分为在执行到某个协程中间时刻和在 poll_future 调度函数期间。当执行到某个协程中间时刻时，控制流发生了转移，那么正在执行的协程将被与这个线程进行绑定，只有下一次调度到这个线程时，才会继续执行这个任务；当控制流回到 poll_future 调度函数时，若已经调度到某个协程但尚未执行，这与上述的情况相同，当还未调度到某个协程，那么即将被调度的协程会在其他的线程内被调度开始执行。这种情况下，转移的目标对象是同一个进程内的其他线程，切换的上下文是线程运行所需要用到的寄存器，尤其是栈指针寄存器。
> 
> （2）
> 

![](./Article/assets/flow.excalidraw.png)

> 在任意时刻发生中断、异常，转移到其他进程中的线程。同上，这里的任意时刻也可以分为两种情况，当前进程内与某个线程绑定了的协程只能等到下一次调度到这个特定的线程才可以继续执行，未绑定的协程则只需要调度到任意的线程即可执行。这种控制权转移属于是进程切换，需要保存的上下文的范围更大，包括地址空间切换。

##### 3.2.2 调度方式（Bitmap，略写）

##### 3.2.3 内核和用户态的协调机制

> 在第二章我们提到了保留了内核线程的接口，在这里起到了很大的作用。

##### 3.2.4 系统调用接口

> 对同步系统调用接口进行更改，利用宏，使得使用的差距变小

### 4. Evalution

1. 串行的 pipe 环
   - 单线程下的测试不比学长的慢
   - 多线程下的测试加速比
2. 独立的 pipe 模拟网络中的长连接
   - 不同优先级的吞吐量
3. 线程与协程进行对比

### 5. Extension and limits

1. 线程中执行的协程不是固定的，可能会导致多线程的情况下不能完全并行。尽管可以通过调整优先级使得某些协程固定在一个线程上执行。
2. CPU 让权的处理，会导致性能的下降，需要进行权衡
3. 协程的错误处理





### 摘抄的一些素材：
- COROUTINES are a programming language mechanism to enable a function to be suspended and resumed.
- They assist with asynchronous programming, for example, where the program is waiting on an external event.