# Steam Price Collector - 云服务器部署与操作指南

本指南将指导您将当前在本地 Mac 上的爬虫代码完整迁移到远程云服务器 (IP: 43.130.15.32) 并设置自动化每日运行。

## 阶段一：准备云服务器环境

1. **登录云服务器**
   使用 SSH 登录到您的云服务器。

2. **安装基础环境**
   服务器需要安装 Python 3.10+ 和 Git。
   *(如果您使用的是 Ubuntu/Debian 服务器)*:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git -y
   ```

3. **迁移代码到服务器**
   您可以选择两种方式将当前代码放上去：
   - **方式 A (推荐)**: 将本文件夹提交到您的私人 Github 仓库，然后在服务器上 `git clone`。
   - **方式 B**: 使用 `scp` 从本地传到服务器：
     ```bash
     scp -r /Users/string/Desktop/steam_collect root@43.130.15.32:/opt/steam_collect
     ```

## 阶段二：配置运行环境

1. **进入项目目录**
   ```bash
   cd /opt/steam_collect  # 假设您放在了这个目录下
   ```

2. **创建并激活 Python 虚拟环境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量 (.env)**
   确认项目根目录下的 `.env` 文件存在，并且 `POCKETBASE_URL` 已经指向了正确的本地地址（如果 PB 和爬虫在同一台云服务器，建议使用 `127.0.0.1` 以加快速度并节省公网流量）。
   ```env
   # .env 文件内容参考
   POCKETBASE_URL=http://127.0.0.1:80
   POCKETBASE_EMAIL=ingerolegrwoodrowf@gmail.com
   POCKETBASE_PASSWORD=4z2vwPCQMUaC3Rt
   STEAM_API_KEY=EFF67271086F40B15F49FDA14C951E34
   LOG_LEVEL=INFO
   ```

## 阶段三：在云端首次运行 (全量抓取)

因为您的 PocketBase 目前是空的，云端部署好后的 **第一件事** 就是开启一次“全量抓取”。

全量抓取会获取 Steam 上所有的 18 万个 App，并在 8 个区域查询价格。由于 Steam 极为严格的限流机制，这个过程会耗时一到两周。

使用 `nohup` 放入后台长驻即可：
```bash
nohup python -m src.cli run-worker > logs/worker_background.log 2>&1 &
```

**如何监控进程？**
- 检查后台日志输出：`tail -f logs/full_run_background.log`
- 检查结构化日志：`tail -f logs/collector_$(date +%Y-%m-%d).log`
- 随时登录您的 PocketBase 管理后台 (`http://43.130.15.32/_/`)，查看 `batch_controls` 集合中的状态 (`status` 将被标记为 `running`)。

**注意：断点续跑机制与每日更新逻辑**

我们使用了非常完善的本地 SQLite (`data/last_prices.db`) 缓存机制。
- **防止中断丢失进度**：每一次向 Steam 请求到一个游戏在某个区域的价格，程序都会在 SQLite 记录 `last_updated`（当前时间戳）。如果在庞大的循环中程序崩溃或服务器重启，您只需再次运行同样的命令。程序一旦发现某个游戏在某个区域在**今天**已经更新过了，它会瞬间跳过网络请求，光速恢复到崩溃前的进度。
- **跨日全量策略**：假设第一次全量抓取用了 15 天（从 4月2日跑到 4月17日）：
  - 跑完之后，SQLite 中记录的 `last_updated` 分布在 4月2日至 4月17日 之间。
  - 第二天（4月18日）如果你跑默认的增量任务 `python -m src.cli nightly-job`，由于日期不同步（并且增量任务只取有变更的游戏），系统会完美过滤出有价格变动或新发布的游戏，并将它们的 `last_updated` 刷新到 4月18日。
  - 如果未来某一天你想再跑一次覆盖全网的大排查 `--full`，它同样会因为日期更新了，而对每个游戏都老老实实查一遍。

## 阶段四：通过批量任务控制进行全自动抓取 (推荐的新模式)

我们已经在云端部署了强大的 **Batch Date Control** (批处理任务调度表)，位于 PocketBase 的 `batch_controls` 集合中。
这个模式将每天的任务拆分成了更小、更精细的区块（按区域拆分），并预生成了未来 5 年的执行队列！

### 1. (首次执行) 生成未来 5 年的任务队列
在 PocketBase 中一键生成所有的批处理记录：
```bash
python scripts/generate_batches.py
```
这会在云端生成约 14,600 条待处理的抓取任务，按国家和每天的时间错开调度。
*注意：脚本只会在表为空时执行，不用担心重复生成。*

### 2. 启动长驻后台的工作进程 (Worker Daemon)
你现在**不再需要**配置复杂的 Crontab 了！只需在后台挂起一个工作进程：
```bash
nohup python -m src.cli run-worker > logs/worker_background.log 2>&1 &
```

**Worker 工作原理：**
1. **自动索取任务**：Worker 每 60 秒轮询一次 PocketBase 的 `batch_controls` 表。
2. **时间判断**：如果当前时间大于等于任务的 `scheduled_time`，它会认领该任务（将状态标记为 `running`）。
3. **独立抓取**：按任务里配置的 `mode` (全量/增量) 和 `region` (cn, us等) 独自抓取，并同步结果。
4. **汇报与防呆**：抓完后标记为 `completed`。如果崩溃则标记为 `failed`。

### 3. 如何在 UI 界面人工干预明天的抓取？
登录你的 PocketBase `http://43.130.15.32/_/`，找到 `batch_controls` 集合：
- **想修改明天跑增量还是全量？** 找到明天对应国家的记录，把 `mode` 从 `incremental` 改为 `full`。
- **想重跑昨天的任务？** 把昨天某条失败的记录的 `status` 从 `failed` 或 `completed` 改回 `pending`，Worker 看到后马上就会认领并重跑。
- **想修改运行时间？** 更改 `scheduled_time` 即可，Worker 只会抓取到达设定时间的任务。

---

### 日常维护命令速查

- **手动跑一次增量** (不查全网，只查变化的游戏)：
  ```bash
  python -m src.cli nightly-job
  ```
- **测试某几个应用** (加 limit 限制数量，验证环境是否畅通)：
  ```bash
  python -m src.cli collect-prices --limit 10
  ```
- **强制刷新今天的所有数据** (无视断点记录强制从 Steam 请求最新价)：
  ```bash
  python -m src.cli nightly-job --full --force-refresh
  ```
