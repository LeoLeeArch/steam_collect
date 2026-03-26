# Steam 促销监控 iOS App（MVP）阶段 1：设计文档

> 目标：先交付 **iOS 监控版**（抓取、缓存、历史价格、候选识别、通知、展示、打开页面），坚持“轻量、本地优先、不依赖数据库”。

---

## 1. 产品边界（Phase 1 / MVP）

### 1.1 做什么
- 定期拉取 Steam 热门游戏候选集合（可配置来源）。
- 拉取每个游戏详情（价格、折扣、描述、链接、图片等）。
- 本地维护价格历史（JSONL），识别“历史最低价 / 接近历史最低价”。
- 识别“可能免费领取且永久保留”的候选（带置信度和理由）。
- 在 App 内提供 Dashboard、列表、详情、历史、设置、诊断页。
- 触发本地通知（高置信免费、史低、可选接近史低）。
- 支持从 App 打开 Steam 网页或 Steam App（URL Scheme + fallback）。

### 1.2 明确不做什么
- 不做 iPhone 端自动点击领取。
- 不做复杂账号系统。
- 不做重型后端、队列、数据库（MySQL/PostgreSQL/MongoDB/Redis）。
- 不做必须在线的 SaaS 架构。
- 不做跨设备实时同步（后续可选 iCloud 同步配置，但非 MVP 必需）。

### 1.3 Phase 2 预留
- 与 macOS companion/helper 通信（例如局域网/云中继任选）以执行“自动领取”流程。
- iOS 端仅做策略与候选输出；执行端放在 Mac，规避 iOS 自动化能力限制。

---

## 2. iOS 限制与应对策略

### 2.1 后台刷新不保证准时
**限制**：BackgroundTasks 由系统调度，不保证固定周期与准点。  
**应对**：
- 设计双通道刷新：`前台手动刷新 + 后台尽力刷新`。
- 所有刷新逻辑幂等化：重复执行不产生错误状态。
- UI 明确显示“最近成功刷新时间 / 数据新鲜度”。

### 2.2 网络与反爬限制
**限制**：Steam 页面结构可能变化、请求可能失败或限流。  
**应对**：
- 多源输入（Top Sellers / Top Played / 用户关注 / 本地白名单）。
- `URLSession` + 超时 + 指数退避重试 + 本地缓存回退。
- 轻量限流（每轮最大请求数、请求间隔、并发上限）。

### 2.3 通知策略
**限制**：通知频繁会打扰用户且可能被关闭。  
**应对**：
- 去重状态文件（已发通知 ID + TTL）。
- 默认只通知高价值事件（高置信免费 + 史低），接近史低可选。

### 2.4 本地存储可靠性
**限制**：无数据库时需要保证文件一致性与可恢复。  
**应对**：
- 原子写入（tmp + replace）。
- 历史采用 append-only JSONL，损坏时可截断恢复。
- 所有关键模型版本化（schemaVersion）。

---

## 3. 总体架构设计

## 3.1 架构风格
- **SwiftUI + MVVM + Observation（iOS 17+）**
- 领域分层：
  1) Presentation（View + ViewModel）
  2) Application（UseCase / Refresh Orchestrator）
  3) Infrastructure（Steam API Client / Parser / FileStore / Notification / BGTask）

## 3.2 核心模块
- `ConfigCenter`：统一配置读取/更新（settings.json）。
- `SteamSourceService`：拉热门候选 appid（多来源聚合）。
- `SteamGameService`：拉详情与价格信息。
- `CacheStore`：热点列表和详情缓存。
- `PriceHistoryStore`：按 appid 写 JSONL 历史。
- `PriceAnalyzer`：史低/接近史低计算。
- `FreeCandidateDetector`：免费永久候选识别（高/中/低）。
- `RefreshCoordinator`：一次刷新总流程编排。
- `NotificationService`：本地通知发送与去重。
- `DiagnosticsLogger`：结构化日志（本地文件）。

## 3.3 文本架构图

```text
[SwiftUI Views]
   -> [ViewModels @Observable]
      -> [RefreshCoordinator]
          -> [SteamSourceService] -> [URLSession]
          -> [SteamGameService]   -> [URLSession]
          -> [CacheStore (JSON)]
          -> [PriceHistoryStore (JSONL)]
          -> [PriceAnalyzer]
          -> [FreeCandidateDetector]
          -> [NotificationService]
          -> [DiagnosticsLogger]
```

---

## 4. 建议目录结构（Xcode 工程内）

```text
SteamPulse/
  App/
    SteamPulseApp.swift
    AppBootstrap.swift
  Core/
    Models/
    Config/
    Utilities/
    Logging/
  Features/
    Dashboard/
    HotList/
    GameDetail/
    PriceHistory/
    Settings/
    Diagnostics/
  Services/
    Networking/
    Sources/
    Parsing/
    Caching/
    PriceHistory/
    Detection/
    Notifications/
    BackgroundRefresh/
    Refresh/
  Storage/
    FileStore/
    StateStore/
  Resources/
    Defaults/
  Tests/
    Unit/
```

本地文件布局（沙盒内）：

```text
Documents/config/settings.json
Application Support/cache/hot_games.json
Application Support/cache/game_details/{appid}.json
Application Support/history/{appid}.jsonl
Application Support/state/seen_free_candidates.json
Application Support/state/notifications_sent.json
Application Support/logs/app.log
```

---

## 5. 数据结构设计（MVP 必备字段）

## 5.1 GameSnapshot（当前快照）
- `appid: Int`
- `name: String`
- `shortDescription: String`
- `currentPrice: Decimal?`（免费可为 0）
- `originalPrice: Decimal?`
- `discountPercent: Int?`
- `currency: String?`
- `isFreeNow: Bool`
- `isCandidateKeepForever: Bool`
- `candidateReason: String?`
- `candidateConfidence: FreeConfidence`（high/medium/low/excluded）
- `storeURL: URL`
- `capsuleImageURL: URL?`
- `tags: [String]`
- `sourceRank: Int?`
- `lastSeenAt: Date`
- `historicalLowPrice: Decimal?`
- `nearHistoricalLow: Bool`
- `priceHistorySummary: PriceHistorySummary`

## 5.2 PriceHistoryPoint（JSONL 行记录）
- `timestamp: Date`
- `price: Decimal`
- `originalPrice: Decimal?`
- `discountPercent: Int?`
- `currency: String`
- `source: String`（如 `steam_api`）

> 仅在“价格或货币变化”时追加，避免重复写入。

## 5.3 Settings
- 热门来源开关与优先级
- 每源抓取上限 N
- 接近史低阈值（默认 3%）
- 通知策略开关
- 重试次数、超时、并发上限
- 手动刷新冷却时间

## 5.4 State 文件
- `seen_free_candidates.json`：已识别候选及最近时间（去重）
- `notifications_sent.json`：已发通知事件（eventId + sentAt + ttl）

---

## 6. 页面结构（信息架构）

## 6.1 Dashboard
- 今日高置信免费候选（卡片）
- 今日史低（列表）
- 今日接近史低（列表）
- 顶部显示：最近刷新时间、刷新状态、手动刷新按钮

## 6.2 热门榜单页
- 分段来源：Top Sellers / Top Played / Watchlist
- 支持排序：折扣力度 / 价格 / 史低状态 / 热门排名
- 每行展示：封面、现价、原价、折扣、史低标签

## 6.3 游戏详情页
- 价格区：当前价 / 原价 / 折扣
- 历史区：历史最低、是否接近、最近变化摘要
- 候选判定区：高/中/低 + 文本理由
- 操作：打开 Steam 页面 / Steam App

## 6.4 历史价格页
- 轻量时间线列表（MVP 可先不画复杂图表）
- 展示关键价格变动点

## 6.5 设置页
- 热门来源配置
- 价格阈值配置
- 通知配置
- 手动刷新
- 后台刷新说明（系统不保证准时）

## 6.6 诊断页
- 最近刷新日志
- 最近错误摘要
- 缓存状态（文件大小、最近更新时间）

---

## 7. 刷新流程设计（前台 + 后台统一）

## 7.1 单次刷新流水线
1. 读取 settings + 上次状态
2. 依据来源配置拉取热门 appid 列表（去重并保留 sourceRank）
3. 对每个 appid 拉详情（受限流/并发控制）
4. 写入详情缓存
5. 写入价格历史（只写变化点）
6. 计算历史最低 / 接近史低
7. 运行免费候选识别
8. 产出 Dashboard 聚合结果
9. 根据通知策略去重后发送本地通知
10. 持久化状态与日志

## 7.2 失败回退
- 单个 appid 失败：记录错误并继续其它项。
- 来源失败：回退到最近缓存，不阻断全流程。
- 全部网络失败：显示“离线缓存数据 + 刷新失败时间”。

## 7.3 频率控制
- 手动刷新最小间隔（例如 3 分钟，可配置）。
- 后台任务设置 earliestBeginDate，但不承诺执行。
- 总请求数上限（例如每次最多 100 个 appid）。

---

## 8. 价格历史策略（无数据库）

## 8.1 文件策略
- 每个 `appid` 一个 `history/{appid}.jsonl`。
- 每行一个 `PriceHistoryPoint`，append-only。
- 初次记录必写；后续仅当 `price/currency/discountPercent` 变化才写。

## 8.2 计算逻辑
- `historicalLowPrice = min(all prices in same currency scope)`
- `isHistoricalLowNow = currentPrice == historicalLowPrice`
- `nearHistoricalLow = currentPrice <= historicalLowPrice * (1 + threshold)`
  - 默认 `threshold = 0.03`

## 8.3 多币种处理
- 默认在“同币种”内比较史低，避免汇率噪声。
- 若币种变化，`priceHistorySummary` 标注“币种切换，谨慎比较”。

## 8.4 新游戏冷启动
- 历史点过少（如 < 3）时标注“历史样本不足”。
- 不误报“史低神价”，可显示“当前最低（样本内）”。

---

## 9. 免费永久候选识别策略

## 9.1 输入信号
- 价格信号：当前价是否为 0。
- 文案信号：描述/公告/商店标签中的关键词。
- 排除信号：试玩、Demo、Free Weekend、临时活动词。

## 9.2 关键词示例
- 永久保留正向词（中英可配置）：
  - `keep forever`, `yours to keep`, `永久保留`, `永久入库`, `领取后永久`
- 临时/排除词：
  - `free weekend`, `trial`, `demo`, `weekend`, `限时试玩`, `测试版`

## 9.3 置信度分级
- **高置信（High）**：
  - `price == 0` 且命中“永久保留”强语义；
  - 无明显排除词；
  - 输出 `candidateReason`（命中词 + 来源位置）。
- **中置信（Medium）**：
  - `price == 0`，但未命中强语义；
  - 或语义不完整（仅“免费”）。
- **低置信 / 排除（Low/Excluded）**：
  - 命中试玩/Demo/Free Weekend 等词；
  - 或被识别为常驻 F2P（不属于“限时领永久”）。

## 9.4 输出要求
- 每个候选必须包含：`confidence + reason + matchedSignals + excludedSignals`。
- UI 明确展示“机器判定，建议用户二次确认”。

---

## 10. 通知策略

- 事件类型：
  1) `free_candidate_high`
  2) `historical_low_reached`
  3) `near_historical_low`（可选）
- 通知去重键建议：`{eventType}:{appid}:{price}:{dateBucket}`
- 默认策略：
  - 高置信免费：开启
  - 史低：开启
  - 接近史低：关闭（用户可开启）

---

## 11. 配置化热门来源设计

## 11.1 来源抽象
定义统一协议 `HotSourceProvider`（阶段 2 代码实现）：
- `fetchTopAppIDs(limit: Int) async throws -> [HotEntry]`

`HotEntry`：
- `appid`
- `rank`
- `source`（topSellers/topPlayed/watchlist/whitelist）

## 11.2 MVP 来源
1. Steam Charts Top Sellers
2. Steam Charts Top Played
3. 用户自定义 watchlist（本地）
4. 本地 whitelist（随 App 预置）

## 11.3 合并策略
- 先按来源优先级采集，再按 appid 去重。
- `sourceRank` 保留最优来源的排名。
- 支持总量截断（前 N）。

---

## 12. 错误处理、缓存、重试与限流

- 网络超时：如 10s（可配置）
- 重试：最多 2~3 次，指数退避（0.8s, 1.6s, 3.2s）
- 并发：如最多 4~6 个详情请求
- 限流：请求间最小间隔（如 200ms）
- 缓存回退：读取最近成功快照
- 诊断日志：记录 source、appid、HTTP 状态、解析错误、耗时

---

## 13. 第二阶段接入 Mac companion 预留

## 13.1 边界分工
- iOS：发现机会、打标签、推送提醒、提供候选任务。
- macOS helper：用户授权后执行自动领取动作（浏览器/Steam 客户端自动化）。

## 13.2 预留接口（iOS 侧）
- 导出候选任务 `ClaimTask`（JSON）：
  - `appid`, `storeURL`, `confidence`, `reason`, `detectedAt`
- 任务状态字段预留：`pending/sent/claimed/failed`
- 传输方式待 Phase 2 选型：
  - 局域网直连（Bonjour + HTTPS）
  - Cloud relay（可选）
  - iCloud Drive 共享文件（轻量备选）

## 13.3 安全与合规
- 默认关闭自动领取联动。
- 用户显式启用并确认风险条款。
- 所有自动动作日志可审计、可撤销。

---

## 14. MVP 验收标准（阶段 1 设计完成定义）

- 边界清晰：iOS 只做监控，不做自动领取。
- 架构可落地：不依赖数据库和重型后端。
- 数据模型覆盖需求字段。
- 刷新流程可覆盖前台/后台。
- 免费候选与史低判定规则可解释。
- 文件存储策略可长期运行并可恢复。
- 已为 Phase 2 的 Mac companion 预留任务接口。

