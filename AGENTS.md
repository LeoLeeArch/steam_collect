# AGENTS.md

## 项目定位
- 本项目目标是构建一个 **iOS 监控版 Steam 工具**：监控热门游戏、免费永久领取候选、历史低价与近史低提醒。
- 产品第一优先级是“轻量、本地优先、可在 Xcode 中直接运行”。

## 技术栈约束（固定）
- 开发语言：`Swift (5.10+)`
- UI 框架：`SwiftUI`
- 架构建议：`MVVM + Observation`
- 网络：`URLSession`
- 后台刷新：`BackgroundTasks`（best effort）
- 通知：`UserNotifications`

> 除非项目维护者明确批准，不得切换到其他主要技术栈。

## 数据存储约束（强制）
- **禁止引入数据库**：不得引入 Core Data、SQLite、Realm、MySQL、PostgreSQL、MongoDB、Redis 等。
- **数据只能保存在本地文件**：
  - 配置：`JSON`
  - 历史：`JSONL`
- 推荐路径：
  - `Documents/config/settings.json`
  - `Application Support/cache/*.json`
  - `Application Support/history/*.jsonl`
  - `Application Support/state/*.json`

## 功能边界（阶段 1）
- 第一阶段仅实现 iOS 端：抓取、缓存、识别、展示、通知、打开详情页。
- **第一阶段不实现自动领取**（不在 iPhone 端做自动点击/自动领取流程）。
- 自动领取能力仅作为后续与 macOS companion 联动的扩展方向。

## 研发与质量要求
- 每次改动都需要补充必要测试或验证：
  - 业务逻辑改动：优先补单元测试。
  - UI/流程改动：至少给出可复现的手动验证步骤。
- 对网络/解析/存储相关变更，需验证：
  - 成功路径
  - 失败回退路径
  - 数据文件写入正确性

## 任务完成时的输出要求
每个任务完成后，必须在说明中包含：
1. 改动摘要（修改了什么、为什么）。
2. 测试与验证结果（执行了哪些命令，是否通过）。
3. **Xcode 验证步骤**（如何在 Xcode/模拟器中验证功能）。

## 提交与 PR 要求
- 提交应聚焦单一目标，commit message 清晰。
- PR 描述需覆盖：
  - 变更动机
  - 主要改动
  - 测试与 Xcode 验证步骤
  - 是否触及上述硬性约束（数据库/本地存储/自动领取边界）
