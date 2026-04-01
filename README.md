# Steam Price Collector

一个稳定、可增量、可恢复的 Steam 多区域价格采集器。

## 特性

- 使用官方推荐的 `IStoreService/GetAppList` 进行增量 Catalog 同步
- 仅对变化的应用采集价格（避免全量暴力采集）
- 保守限流 + 重试 + 错误率自适应
- 支持断点续跑和失败重试
- 输出分区 JSONL，便于后续导入数据库
- 完整的运行元数据记录

## 项目结构

```
steam_price_collector/
├── src/              # 核心代码
├── config/           # 配置文件
├── data/             # 所有输出数据
│   ├── catalog/      # 应用清单 (dt=YYYY-MM-DD/)
│   ├── prices/       # 价格数据 (dt=YYYY-MM-DD/cc=xx.jsonl)
│   ├── runs/         # 运行记录
│   └── state/        # 状态和 checkpoint
├── logs/
├── scripts/
└── tests/
```

## 快速开始

1. 创建并激活 conda 环境（已存在 myenv）
```bash
conda activate myenv
pip install -r requirements.txt
```

2. 复制配置文件
```bash
cp .env.example .env
```

3. 首次全量同步 Catalog
```bash
python -m src.cli full-sync-catalog
```

4. 运行夜间任务（推荐）
```bash
python -m src.cli nightly-job --regions us cn gb jp de
```

## CLI 命令

- `full-sync-catalog` - 首次全量同步应用清单
- `incremental-sync-catalog` - 每日增量同步
- `collect-prices` - 采集价格（需先同步 catalog）
- `nightly-job` - 一键夜间任务（catalog增量 + 价格采集）
- `resume-run --run-id <id>` - 恢复失败的运行
- `validate-jsonl` - 验证输出文件

## 后续计划

- 数据库导入脚本（MySQL/PostgreSQL）
- 监控告警
- 更多区域支持
- 价格历史分析工具

## 注意事项

- 请遵守 Steam 使用条款
- 保持保守并发，避免被封禁
- 建议夜间低峰期运行
