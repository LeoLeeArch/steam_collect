# 阶段 2 + 阶段 3 实施说明

## 1) 完整目录树

```text
.
├── SteamPulse.xcodeproj/
│   └── project.pbxproj
├── SteamPulse/
│   ├── App/
│   │   ├── AppContainer.swift
│   │   ├── RootTabView.swift
│   │   └── SteamPulseApp.swift
│   ├── Core/
│   │   ├── Config/
│   │   │   ├── FileStore.swift
│   │   │   └── SettingsStore.swift
│   │   └── Models/
│   │       ├── GameModels.swift
│   │       └── Settings.swift
│   ├── Features/
│   │   ├── Dashboard/
│   │   │   ├── DashboardView.swift
│   │   │   └── DashboardViewModel.swift
│   │   ├── HotList/
│   │   │   ├── HotListView.swift
│   │   │   └── HotListViewModel.swift
│   │   └── Settings/
│   │       ├── SettingsView.swift
│   │       └── SettingsViewModel.swift
│   ├── Info.plist
│   ├── Resources/
│   └── Services/
│       ├── Caching/
│       │   └── CacheStore.swift
│       ├── Networking/
│       │   └── NetworkClient.swift
│       ├── Refresh/
│       │   └── RefreshCoordinator.swift
│       └── Sources/
│           ├── GameDetailService.swift
│           ├── HotSourceProvider.swift
│           └── SteamChartsSourceProvider.swift
├── docs/
│   ├── phase1_design.md
│   └── stage2_3_init_and_fetch.md
└── .gitkeep
```

## 2) Xcode 项目建议结构

- Target: `SteamPulse`（iOS 17+，SwiftUI App lifecycle）。
- 目录分层：
  - `App`：入口与依赖组装
  - `Core`：基础模型、配置、文件读写
  - `Services`：网络、数据源、缓存、刷新编排
  - `Features`：页面和 ViewModel
- 当前已建立 3 个页面骨架：Dashboard、热门榜单、设置。

## 3) 阶段 2（项目初始化）完成项

- 建立 `SteamPulse.xcodeproj` 可直接在 Xcode 打开。
- 建立 SwiftUI App 入口、Tab 导航、三页骨架。
- 建立设置模型与本地 `settings.json` 存储服务。

### 阶段 2 Xcode 验证步骤
1. 在 macOS 上打开 `SteamPulse.xcodeproj`。
2. 选择 iPhone 15 模拟器（或任意 iOS 17+ 模拟器）。
3. Build (`⌘B`)。
4. Run (`⌘R`)。
5. 预期：出现 3 个 Tab（首页/热门/设置），可切换页面；设置页可保存配置。

## 4) 阶段 3（抓取与缓存）完成项

- `NetworkClient`：基础 GET + timeout + HTTP 状态校验。
- `SteamChartsSourceProvider`：抓取 Top Sellers / Most Played 页面并提取 appid。
- `GameDetailService`：调用 `appdetails` 接口补全游戏详情。
- `CacheStore`：将热门快照缓存到 `Application Support/cache/hot_games.json`。
- `RefreshCoordinator`：串联“来源抓取 -> 详情抓取 -> 缓存写入 -> 返回 UI”。

### 阶段 3 Xcode 验证步骤
1. 首次运行 App，进入首页或热门页，点击“刷新”。
2. 观察列表由空变为数据（网络可用时）。
3. 重新启动 App，若网络断开仍可看到上次缓存（回退加载）。
4. 在 macOS Console 查看日志或断点确认：
   - 先命中热门来源抓取
   - 再命中详情抓取
   - 最后写入缓存

## 5) 明确未实现项

- 自动领取（iPhone 端）未实现，且本阶段不实现。
- BackgroundTasks、通知、历史价格与免费候选引擎留到后续阶段。
