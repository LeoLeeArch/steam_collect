import Foundation

struct AppSettings: Codable {
    var schemaVersion: Int = 1
    var selectedSources: [HotSourceType] = [.topSellers, .topPlayed]
    var topLimitPerSource: Int = 30
    var requestTimeoutSeconds: Double = 10
    var requestRetryCount: Int = 2
    var requestIntervalMilliseconds: Int = 200
    var maxConcurrentRequests: Int = 4
    var minRefreshIntervalSeconds: TimeInterval = 180

    // 仅配置展示，通知能力后续阶段接入
    var notifyHistoricalLow: Bool = true
    var notifyNearHistoricalLow: Bool = false

    static let `default` = AppSettings()
}
