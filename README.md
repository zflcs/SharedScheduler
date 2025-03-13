# COPS

COPS is a new concurrency model. It employs a priority-based coroutine model as the fundamental task unit, replacing the traditional multi-threading model in scenarios with high concurrency, and offers a unified priority-based scheduling framework for both kernel and user space coroutines.

It was accepted at [CIT-2024](https://smartconf24.org/cit2024/).

The details about COPS are shown below:

- [Paper](./cops.pdf)
- [Data](./cit2024/assets/)
- [Implementation](https://github.com/zflcs/rCore-N/tree/e6989fb928d7b05cf1cd45859d03cb9251edc996)

```latex
@inproceedings{zhao_cops_2024,
	address = {Chengdu, China},
	title = {{COPS}: {A} coroutine-based priority scheduling framework perceived by the operating system},
	publisher = {IEEE},
	author = {Zhao, Fangliang and Liao, Donghai and Wu, Jingbang and Lu, Huimei and Xiang, Yong},
	month = dec,
	booktitle = {2024 International Conference on Ubiquitous Computing and Communications (IUCC)},
	year = {2024},
}
```

## Contact

For any questions about COPS, please email zfl22@mails.tsinghua.edu.cn.
