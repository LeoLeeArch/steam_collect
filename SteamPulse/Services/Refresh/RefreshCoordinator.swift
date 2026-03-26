import Foundation

@MainActor
final class RefreshCoordinator {
    private let settingsStore: SettingsStore
    private let hotSourceService: HotSourceService
    private let gameDetailService: GameDetailService
    private let cacheStore: CacheStore
    private let priceHistoryStore: PriceHistoryStore
    private let priceAnalyzer: PriceAnalyzer
    private let refreshStatusStore: RefreshStatusStore

    init(
        settingsStore: SettingsStore,
        hotSourceService: HotSourceService,
        gameDetailService: GameDetailService,
        cacheStore: CacheStore,
        priceHistoryStore: PriceHistoryStore,
        priceAnalyzer: PriceAnalyzer,
        refreshStatusStore: RefreshStatusStore
    ) {
        self.settingsStore = settingsStore
        self.hotSourceService = hotSourceService
        self.gameDetailService = gameDetailService
        self.cacheStore = cacheStore
        self.priceHistoryStore = priceHistoryStore
        self.priceAnalyzer = priceAnalyzer
        self.refreshStatusStore = refreshStatusStore
    }

    func refresh() async throws -> [GameSnapshot] {
        let settings = settingsStore.load()
        let hotEntries: [HotEntry]
        do {
            hotEntries = try await hotSourceService.fetchAll(
                sources: settings.selectedSources,
                limit: settings.topLimitPerSource,
                timeout: settings.requestTimeoutSeconds,
                retries: settings.requestRetryCount
            )
        } catch {
            refreshStatusStore.save(
                RefreshStatus(
                    updatedAt: Date(),
                    outcome: .failed,
                    totalEntries: 0,
                    succeededDetails: 0,
                    failedDetails: 0,
                    message: "热门抓取失败：\(error.localizedDescription)"
                )
            )
            throw error
        }

        var snapshots: [GameSnapshot] = []
        var failedDetails = 0
        let limiter = RateLimiter(minInterval: TimeInterval(settings.requestIntervalMilliseconds) / 1000.0)

        for entry in hotEntries.prefix(settings.topLimitPerSource) {
            await limiter.waitIfNeeded()

            var detail = await gameDetailService.fetchDetail(
                appid: entry.appid,
                sourceRank: entry.rank,
                timeout: settings.requestTimeoutSeconds,
                retries: settings.requestRetryCount
            )

            if detail.currentPrice == nil && detail.originalPrice == nil {
                failedDetails += 1
            }

            try? priceHistoryStore.appendIfNeeded(appid: detail.appid, snapshot: detail)
            let history = (try? priceHistoryStore.load(appid: detail.appid)) ?? []
            let analysis = priceAnalyzer.analyze(currentPrice: detail.currentPrice, history: history)
            detail.historicalLowPrice = analysis.historicalLow
            detail.nearHistoricalLow = analysis.nearHistoricalLow

            snapshots.append(detail)
        }

        try cacheStore.saveHotGames(snapshots)
        refreshStatusStore.save(
            RefreshStatus(
                updatedAt: Date(),
                outcome: .success,
                totalEntries: snapshots.count,
                succeededDetails: max(0, snapshots.count - failedDetails),
                failedDetails: failedDetails,
                message: failedDetails == 0 ? "刷新成功" : "刷新完成，但有部分详情回退为占位数据"
            )
        )
        return snapshots
    }

    func loadCached() -> [GameSnapshot] {
        cacheStore.loadHotGames()?.items ?? []
    }
}
