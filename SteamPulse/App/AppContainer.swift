import Foundation

struct AppContainer {
    let settingsStore: SettingsStore
    let hotSourceService: HotSourceService
    let gameDetailService: GameDetailService
    let cacheStore: CacheStore
    let priceHistoryStore: PriceHistoryStore
    let priceAnalyzer: PriceAnalyzer
    let refreshStatusStore: RefreshStatusStore
    let refreshCoordinator: RefreshCoordinator

    static func bootstrap() -> AppContainer {
        let fileStore = FileStore()
        let settingsStore = SettingsStore(fileStore: fileStore)
        let networkClient = NetworkClient()
        let steamChartsSource = SteamChartsSourceProvider(networkClient: networkClient)
        let hotSourceService = HotSourceService(providers: [steamChartsSource])
        let gameDetailService = GameDetailService(networkClient: networkClient)
        let cacheStore = CacheStore(fileStore: fileStore)
        let priceHistoryStore = PriceHistoryStore(fileStore: fileStore)
        let priceAnalyzer = PriceAnalyzer()
        let refreshStatusStore = RefreshStatusStore(fileStore: fileStore)

        let refreshCoordinator = RefreshCoordinator(
            settingsStore: settingsStore,
            hotSourceService: hotSourceService,
            gameDetailService: gameDetailService,
            cacheStore: cacheStore,
            priceHistoryStore: priceHistoryStore,
            priceAnalyzer: priceAnalyzer,
            refreshStatusStore: refreshStatusStore
        )

        return AppContainer(
            settingsStore: settingsStore,
            hotSourceService: hotSourceService,
            gameDetailService: gameDetailService,
            cacheStore: cacheStore,
            priceHistoryStore: priceHistoryStore,
            priceAnalyzer: priceAnalyzer,
            refreshStatusStore: refreshStatusStore,
            refreshCoordinator: refreshCoordinator
        )
    }
}
