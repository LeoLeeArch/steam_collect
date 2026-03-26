# SteamPulse 执行计划（先规划，不写代码）

> 目标：基于当前仓库，明确如何把项目组织成可持续迭代的 iOS SwiftUI 应用，并给出 MVP（热门监控 + 免费永久候选识别 + 历史低价跟踪）的分阶段落地路径。

---

## 1）当前仓库如何组织成一个 iOS SwiftUI 项目

当前仓库已经具备 iOS 工程雏形（`SteamPulse.xcodeproj` + `App/Core/Features/Services`）。建议保留并强化“按领域 + 分层”结构：

- **App 层（装配）**
  - 负责入口、依赖注入、全局生命周期（App 启动、前后台事件）。
  - 不放业务逻辑，只做 wiring。
- **Core 层（基础能力）**
  - 通用模型、配置、文件 IO、日志、错误定义、时间与货币工具。
  - 保持独立，可被多 Feature/Service 复用。
- **Services 层（数据与规则）**
  - 网络抓取、来源适配、缓存、历史价格写入与计算、规则引擎（免费候选）。
  - 通过协议解耦，便于 mock 与测试。
- **Features 层（UI + ViewModel）**
  - Dashboard、热门榜单、详情、历史、设置、诊断。
  - 每个 Feature 只依赖抽象用例，不直接依赖底层实现细节。
- **Storage 约束（本地优先）**
  - JSON/JSONL 为唯一持久化主路径，不引入数据库。

建议补齐关键工程约束：
- 所有 Service 协议化（`protocol + impl`）。
- ViewModel 只接 UseCase，不直接调用网络层。
- 每次刷新产生统一 `RefreshReport`（成功数/失败数/缓存回退/通知数）。
- 统一错误域：`NetworkError/ParseError/StorageError/RuleError`。

---

## 2）MVP：Steam 热门监控 + 免费永久候选 + 历史低价跟踪（最小可行版）

### MVP 功能闭环
1. **热门监控**
   - 从 Top Sellers / Top Played 抓取前 N 个 appid。
   - 拉取 appdetails，得到游戏名、价格、折扣、链接、封面。
   - 列表展示 + 手动刷新 + 缓存回退。

2. **免费永久候选识别（规则版）**
   - 输入：当前价格、描述文案、标题关键词。
   - 输出：`high/medium/low/excluded` + reason。
   - 高置信才通知，中低置信只展示标签。

3. **历史最低价跟踪（无数据库）**
   - 每个 appid JSONL 历史文件，仅在“价格变化”时写入。
   - 计算：历史最低价、是否等于史低、是否接近史低（默认 3%）。
   - 在详情页和 Dashboard 显示结果。

### MVP 非目标（明确不做）
- iPhone 端自动领取。
- 自建后台与账号体系。
- 多端实时同步与复杂分享。

---

## 3）目录结构建议

```text
SteamPulse/
  App/
    SteamPulseApp.swift
    AppContainer.swift
    AppLifecycle.swift
  Core/
    Models/
      GameSnapshot.swift
      PriceHistoryPoint.swift
      Settings.swift
      RefreshReport.swift
    Config/
      SettingsStore.swift
      FeatureFlags.swift
    Storage/
      FileStore.swift
      JSONCodec.swift
    Logging/
      Logger.swift
    Errors/
      AppError.swift
  Services/
    Networking/
      NetworkClient.swift
      RetryPolicy.swift
      RateLimiter.swift
    Sources/
      HotSourceProvider.swift
      SteamChartsSourceProvider.swift
      WatchlistSourceProvider.swift
    GameDetails/
      GameDetailService.swift
      GameDetailParser.swift
    Caching/
      CacheStore.swift
    History/
      PriceHistoryStore.swift
      PriceAnalyzer.swift
    Detection/
      FreeCandidateDetector.swift
      KeywordRules.swift
    Refresh/
      RefreshCoordinator.swift
  Features/
    Dashboard/
    HotList/
    GameDetail/
    PriceHistory/
    Settings/
    Diagnostics/
  Resources/
    Defaults/
      settings.default.json
      keyword_rules.json
  Tests/
    Unit/
      Services/
      Detection/
      History/
      Storage/
```

---

## 4）数据文件结构建议（本地文件）

> 路径遵循 iOS 沙盒：`Documents` + `Application Support`。

### 配置类
- `Documents/config/settings.json`
  - 用户可修改：来源开关、抓取上限、阈值、通知策略、刷新间隔。

### 缓存类
- `Application Support/cache/hot_games.json`
  - 最近一次聚合结果（列表页/首页快速展示）。
- `Application Support/cache/game_details/{appid}.json`
  - 游戏详情缓存（详情页离线回退）。

### 历史类
- `Application Support/history/{appid}.jsonl`
  - 每行一个价格点（时间戳、币种、价格、折扣、来源）。
  - 仅在关键变化时追加，避免膨胀。

### 状态类
- `Application Support/state/seen_free_candidates.json`
  - 候选去重（避免重复告警）。
- `Application Support/state/notifications_sent.json`
  - 通知事件去重与 TTL。
- `Application Support/state/refresh_state.json`
  - 最近刷新结果、错误摘要、数据新鲜度。

### 日志类
- `Application Support/logs/app.log`
  - 结构化日志（JSON 行），用于诊断页展示。

---

## 5）分 5 个阶段的开发计划

## 阶段 A：工程稳态化（Project Hardening）
**目标**：把现有骨架整理为稳定可迭代工程。
- 固化分层与命名规范。
- 补齐协议抽象与依赖注入边界。
- 增加统一错误类型、日志接口。
- 加入默认配置文件与首次启动初始化逻辑。

**交付**：工程可稳定构建运行；页面骨架完整可导航。

## 阶段 B：抓取与缓存 MVP
**目标**：稳定拿到热门游戏基础数据并缓存回退。
- 热门来源抓取（Top Sellers / Top Played）。
- appdetails 拉取与解析。
- 超时、重试、限流。
- 缓存写入/读取与失败回退。

**交付**：热门列表可刷新并展示；离线可见上次缓存。

## 阶段 C：历史价格系统 MVP
**目标**：无数据库下完成历史价格记录与史低分析。
- JSONL 结构与 append-only 写入。
- 去重写入（相同价格不重复写）。
- 史低 / 接近史低计算。
- Dashboard 与详情页展示价格结论。

**交付**：可看到历史最低与近史低标签，支持样本不足标记。

## 阶段 D：免费永久候选识别 MVP
**目标**：可解释的规则引擎上线。
- 关键词规则（正向/排除）配置化。
- 置信度分级（high/medium/low/excluded）。
- 候选 reason、命中词与排除词展示。
- 与列表/详情页集成标签。

**交付**：候选识别可用且具可解释性；误报可通过规则快速调整。

## 阶段 E：通知、后台刷新与验收
**目标**：形成“监控 -> 提醒 -> 打开详情”的闭环。
- 本地通知（高置信免费、史低、可选近史低）。
- BackgroundTasks 接入（best effort）。
- 手动刷新与后台刷新协调，避免频繁请求。
- 诊断页（刷新记录、错误摘要、缓存状态）。

**交付**：MVP 端到端可用，满足 iOS 监控版目标。

---

## 6）每个阶段验收标准

## 阶段 A 验收
- Xcode 能稳定 build/run（iOS 17+）。
- 三个主页面（首页/热门/设置）可导航。
- 配置可读写并持久化。
- 代码分层清晰，无跨层硬耦合。

## 阶段 B 验收
- 手动刷新可拉取热门并展示。
- 网络失败时可回退缓存。
- 请求具备 timeout + retry + rate limit。
- 诊断可看到来源抓取与详情抓取结果。

## 阶段 C 验收
- 历史价格文件按 appid 生成。
- 相同价格不重复写入。
- 史低与近史低计算结果正确（含单元测试）。
- 新游戏样本不足时有明确提示。

## 阶段 D 验收
- 候选识别输出 `confidence + reason`。
- 高/中/低/排除分类可通过测试样例验证。
- UI 可展示判定依据，不是黑盒结果。

## 阶段 E 验收
- 高置信免费和史低事件能发本地通知。
- 通知去重有效，无短时重复轰炸。
- 后台刷新失败不影响前台手动刷新。
- 诊断页可追溯最近刷新与通知行为。

---

## 备注（边界重申）
- 本计划只覆盖 **iOS 监控版 MVP**。
- 自动领取属于 Phase 2（Mac companion）能力，不在当前 5 阶段实现范围内。
