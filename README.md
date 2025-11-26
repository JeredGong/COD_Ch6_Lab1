# COD_Ch6_Lab1：Mandelbrot 多线程实验

本项目是 **武汉大学计算机学院《计算机组成与体系结构》课程第六章实验一** 的配套代码。  
实验目标是使用 C++ 多线程（pthread）实现 Mandelbrot 集的并行计算，对比串行与并行版本性能，并使用 Python 脚本进行可视化分析。

主要代码位于 `mandelbrot_threads/` 目录，公共工具代码位于 `common/` 目录。

## 环境说明

推荐环境（Linux / WSL / macOS）：

- C/C++ 编译器：`g++`（支持 C++11 及以上）
- 构建工具：`make`
- 线程库：`pthread`（Linux/WSL 默认自带）
- Python：`Python 3.8+`
- Python 第三方库：
  - `matplotlib`（通过 `requirements.txt` 安装）

安装 Python 依赖（在项目根目录或 `mandelbrot_threads/` 下）：

```bash
cd mandelbrot_threads
pip install -r requirements.txt
```

## 代码结构简要说明

- `common/`
  - `CycleTimer.h`：高精度计时工具
  - `ppm.cpp`：PPM 图像输出
  - `tasksys.cpp`：任务系统（若实验需要）
- `mandelbrot_threads/`
  - `main.cpp`：程序入口，命令行参数解析、计时、结果校验
  - `mandelbrot.cpp`：Mandelbrot 串行和多线程核心计算（需要在此完成实验）
  - `thread_timing.h` / `thread_timing.cpp`：可选线程级计时与 CSV 记录
  - `Makefile`：使用 `g++` + `make` 构建 `mandelbrot` 可执行文件
  - `plot_speedup.py`：批量运行不同线程数并绘制加速比曲线
  - `plot_thread_load.py`：基于线程计时 CSV 绘制各线程负载分布
  - `requirements.txt`：Python 依赖

## 快速开始

### 1. 编译程序

在项目根目录执行：

```bash
cd mandelbrot_threads
make
```

成功后会生成可执行文件：

```bash
./mandelbrot
```

### 2. 运行 Mandelbrot 程序

基本用法：

```bash
./mandelbrot
```

常用参数：

- 指定线程数：

  ```bash
  ./mandelbrot --threads 8
  ```

- 指定视角（不同放大/平移配置）：

  ```bash
  ./mandelbrot --view 2
  ```

程序会输出串行与多线程运行时间，并生成：

- `mandelbrot-serial.ppm`
- `mandelbrot-thread.ppm`

可用图像查看器打开对比效果。

### 3. 绘制加速比曲线（可选）

在 `mandelbrot_threads/` 目录下：

```bash
python3 plot_speedup.py --show
```

脚本会：

- 调用 `./mandelbrot`，分别用多个线程数运行
- 解析输出中的串行/并行时间与加速比
- 将数据写入 `speedup_view1.csv`
- 使用 matplotlib 绘制“加速比 vs 线程数”曲线（加上 `--png` 可保存为图片）

常用参数说明（`plot_speedup.py`）：

- `--exe PATH`  
  指定 `mandelbrot` 可执行文件路径，默认为脚本所在目录下的 `./mandelbrot`。
- `--view N`  
  指定传给 `mandelbrot` 的视角编号（对应 `./mandelbrot --view N`），默认 `2`。
- `--threads T1 T2 ...`  
  指定需要测试的线程数列表，默认为 `1 2 4 6 8 12 14 16`。  
  示例：`--threads 1 2 4 8 16 32`
- `--csv PATH`  
  指定保存测量结果的 CSV 文件路径，默认在脚本目录下生成 `speedup_view1.csv`。
- `--show`  
  显示加速比曲线的窗口（需要安装 `matplotlib`）。
- `--png PATH`  
  将加速比曲线保存为 PNG 文件而不是弹窗显示，例如：`--png speedup.png`。
- `extra`（位置参数）  
  额外传给 `mandelbrot` 的参数，需要用 `--` 与脚本参数分隔，例如：

  ```bash
  python3 plot_speedup.py --view 2 --threads 1 2 4 -- --threads 8
  ```

  其中 `--` 之后的部分会原样附加到 `./mandelbrot` 命令行末尾。

### 4. 绘制线程负载分布（可选）

1. **启用线程级计时**：编译时定义 `ENABLE_THREAD_TIMING`：

   ```bash
   cd mandelbrot_threads
   make clean
   make CXXFLAGS=-DENABLE_THREAD_TIMING
   ```

2. **运行程序生成线程计时 CSV**：

   ```bash
   ./mandelbrot --threads 8 --view 1
   ```

   将在当前目录生成 `thread_timings.csv`。

3. **绘制线程负载图**：

   ```bash
   python3 plot_thread_load.py --show
   # 或保存为 PNG
   python3 plot_thread_load.py --png thread_load.png
   ```

该图可以帮助分析不同线程之间负载是否均衡，为后续优化提供参考。

常用参数说明（`plot_thread_load.py`）：

- `--csv PATH`  
  指定输入的线程计时 CSV 文件路径，默认为当前/脚本目录下的 `thread_timings.csv`。
- `--invoke`  
  在绘图前自动调用 `mandelbrot` 多次，以生成/更新 CSV 文件；不加该参数时，仅读取已有 CSV。
- `--exe PATH`  
  指定 `mandelbrot` 可执行文件路径，默认为脚本所在目录下的 `./mandelbrot`。
- `--threads N`  
  配合 `--invoke` 使用：指定运行 `mandelbrot` 时的线程数（即 `./mandelbrot --threads N`）。
- `--view N`  
  配合 `--invoke` 使用：指定运行 `mandelbrot` 时的视角编号（默认 `1`）。
- `--repeat K`  
  配合 `--invoke` 使用：重复运行 `mandelbrot` 的次数，默认 `1`。可以用来收集多次运行的采样。
- `--run-id ID`  
  从 CSV 中选择要可视化的 `run_id`，默认选择最新（最大的 `run_id`）。
- `--sort {duration,thread}`  
  控制柱状图的排序方式：  
  - `duration`：按线程运行时间从长到短排序（更容易看出负载不均衡）  
  - `thread`：按线程编号排序
- `--show`  
  显示线程负载分布图窗口。
- `--png PATH`  
  将线程负载分布图保存为 PNG 文件，例如：`--png thread_load.png`。
- `extra`（位置参数）  
  追加传给 `mandelbrot` 的额外参数，同样需要用 `--` 与脚本自身参数分隔，例如：

  ```bash
  python3 plot_thread_load.py --invoke --threads 8 --view 1 --repeat 3 -- --threads 8
  ```

  这样可以在启用计时的前提下，对不同参数组合进行多次采样并统一画图。

