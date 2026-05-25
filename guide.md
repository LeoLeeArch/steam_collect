# Steam Price Collector 使用指南

## 1. 项目功能概览

这个项目是一个 Steam 多区域价格采集器，目标是稳定、增量、可恢复地采集 Steam 应用清单和多地区价格数据。

当前代码的核心流程是：

1. 通过 Steam 官方公共接口 `IStoreService/GetAppList` 同步应用 Catalog。
2. 支持首次全量同步和后续增量同步。
3. 将应用清单按日期写入 `data/catalog/dt=YYYY-MM-DD/apps.jsonl`。
4. 使用 checkpoint 保存同步进度，便于后续恢复或追踪状态。
5. 预留价格采集、夜间任务、失败恢复和 JSONL 校验等 CLI 命令。

需要注意：当前代码里 Catalog 同步已经有实际实现；`collect-prices`、`nightly-job`、`resume-run`、`validate-jsonl` 目前只是在 CLI 中注册并打印提示，具体采集/恢复/校验逻辑仍是待实现状态。

## 2. 目录说明

```text
steam_collect/
├── config/
│   └── config.yaml          # Steam 接口、采集区域、限流、路径和日志配置
├── data/
│   ├── catalog/             # Catalog 输出目录
│   ├── prices/              # 价格输出目录，当前价格采集逻辑尚未实现
│   ├── runs/                # 运行元数据输出目录
│   └── state/               # checkpoint 和增量同步状态
├── logs/                    # 日志目录
├── scripts/
│   └── nightly.bat          # Windows 夜间任务脚本
├── src/
│   ├── catalog.py           # Catalog 同步主逻辑
│   ├── cli.py               # 命令行入口
│   ├── config.py            # 配置读取和路径管理
│   ├── models.py            # Pydantic 数据模型
│   ├── retry.py             # 限流和重试逻辑
│   └── utils.py             # JSONL、checkpoint、时间等工具函数
├── tests/
├── .env.example             # 环境变量示例
├── pyproject.toml           # Python 项目配置
├── requirements.txt         # 依赖列表
└── README.md
```

## 3. 环境准备

项目要求 Python 3.11 或更高版本。依赖包括 `aiohttp`、`pyyaml`、`pydantic`、`structlog`、`tenacity` 等。

如果使用 conda，可以参考项目现有说明：

```powershell
conda activate myenv
pip install -r requirements.txt
```

如果不使用 conda，也可以使用普通虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

复制环境变量示例文件：

```powershell
Copy-Item .env.example .env
```

`.env.example` 当前只包含可选日志级别：

```env
LOG_LEVEL=INFO
```

## 4. 配置文件

主配置文件是 `config/config.yaml`。

默认采集区域：

```yaml
collector:
  regions:
    - us
    - cn
    - gb
    - jp
    - de
```

默认货币映射：

```yaml
collector:
  default_currency:
    us: "USD"
    cn: "CNY"
    gb: "GBP"
    jp: "JPY"
    de: "EUR"
```

默认限流配置较保守：

```yaml
rate_limit:
  max_workers: 3
  requests_per_second_per_worker: 0.8
  max_retries: 6
  cooldown_seconds: 30
```

输出路径默认都在 `data/` 下：

```yaml
paths:
  data_root: "data"
  catalog_dir: "data/catalog"
  prices_dir: "data/prices"
  runs_dir: "data/runs"
  state_dir: "data/state"
  logs_dir: "logs"
```

## 5. 执行方式

以下命令都需要在项目根目录执行：

```powershell
cd C:\Users\2508118004\Desktop\steam_collect
```

### 5.1 查看 CLI 帮助

```powershell
python -m src.cli --help
```

### 5.2 首次全量同步 Catalog

首次使用时建议先执行全量同步：

```powershell
python -m src.cli full-sync-catalog
```

执行后会调用 Steam Catalog API，并把应用清单写入：

```text
data/catalog/dt=YYYY-MM-DD/apps.jsonl
```

同时会写入运行记录：

```text
data/runs/crawl_run_<run_id>.json
```

并更新 checkpoint：

```text
data/state/checkpoint.json
```

### 5.3 后续增量同步 Catalog

后续日常同步可以执行：

```powershell
python -m src.cli incremental-sync-catalog
```

增量同步会读取：

```text
data/state/last_if_modified_since.json
```

并将其作为 Steam API 的 `if_modified_since` 参数，尽量只拉取变化过的应用。

### 5.4 采集价格

CLI 中已经注册了价格采集命令：

```powershell
python -m src.cli collect-prices --regions us cn gb jp de
```

但当前源码中该命令的实际逻辑尚未实现，只会打印：

```text
collect-prices command registered (implementation pending)
```

因此目前不能依赖它生成价格数据。

### 5.5 夜间任务

CLI 中已经注册夜间任务命令：

```powershell
python -m src.cli nightly-job --regions us cn gb jp de
```

项目也提供了 Windows 批处理脚本：

```powershell
.\scripts\nightly.bat
```

脚本内容等价于：

```bat
call conda activate myenv
python -m src.cli nightly-job --regions us cn gb jp de
```

但当前 `nightly-job` 命令的具体业务逻辑尚未实现，只会生成 `run_id` 并打印待实现提示。

### 5.6 恢复失败任务

CLI 中已注册恢复命令：

```powershell
python -m src.cli resume-run --run-id <run_id>
```

当前该命令仍为待实现状态，只会打印提示信息。

### 5.7 校验 JSONL

CLI 中已注册 JSONL 校验命令：

```powershell
python -m src.cli validate-jsonl
```

当前该命令仍为待实现状态，只会打印提示信息。

## 6. 主要输出文件

### 6.1 Catalog 数据

Catalog 同步输出路径：

```text
data/catalog/dt=YYYY-MM-DD/apps.jsonl
```

每一行是一条 Steam 应用记录，主要字段来自 `SteamAppCatalog`：

```json
{
  "appid": 123,
  "name": "Example Game",
  "type": "game",
  "is_free": false,
  "coming_soon": false,
  "release_date": "2024-01-01",
  "store_url": "https://store.steampowered.com/app/123",
  "steam_last_modified": 1710000000,
  "steam_price_change_number": 100,
  "first_seen_at": "2026-04-23T00:00:00+00:00",
  "last_seen_at": "2026-04-23T00:00:00+00:00",
  "raw_basic_json": {}
}
```

### 6.2 运行记录

运行记录输出路径：

```text
data/runs/crawl_run_<run_id>.json
```

虽然扩展名是 `.json`，代码中实际使用 JSONL append 的方式写入。

### 6.3 Checkpoint

checkpoint 输出路径：

```text
data/state/checkpoint.json
```

主要记录：

```json
{
  "last_run_id": "20260423_120000",
  "last_catalog_sync": "2026-04-23T04:00:00+00:00",
  "last_appid": 123456,
  "last_if_modified_since": 0,
  "total_apps_known": 1000
}
```

### 6.4 增量同步状态

增量同步时间戳路径：

```text
data/state/last_if_modified_since.json
```

用于后续 `incremental-sync-catalog`。

## 7. 当前已实现与待实现

已实现：

```text
python -m src.cli full-sync-catalog
python -m src.cli incremental-sync-catalog
```

已注册但待实现：

```text
python -m src.cli collect-prices --regions us cn gb jp de
python -m src.cli nightly-job --regions us cn gb jp de
python -m src.cli resume-run --run-id <run_id>
python -m src.cli validate-jsonl
```

## 8. 注意事项

1. 该项目会访问 Steam 公共接口，请遵守 Steam 使用条款。
2. 默认限流较保守，建议不要随意提高并发或请求频率。
3. 首次同步可能产生较多网络请求，建议在网络稳定时执行。
4. 当前价格采集逻辑尚未完成，`data/prices/` 目前不会由现有实现自动生成有效价格数据。
5. 如果需要自动定时运行，可以基于 `scripts/nightly.bat` 配合 Windows 任务计划程序，但要先补完 `nightly-job` 的实际逻辑。

