import Foundation

struct HotEntry: Codable, Hashable, Identifiable {
    let appid: Int
    let rank: Int
    let source: HotSourceType

    var id: Int { appid }
}

enum HotSourceType: String, Codable, CaseIterable {
    case topSellers
    case topPlayed
    case watchlist
    case whitelist
}

struct PriceHistoryPoint: Codable, Hashable {
    let timestamp: Date
    let price: Decimal
    let originalPrice: Decimal?
    let discountPercent: Int?
    let currency: String
}

struct GameSnapshot: Codable, Identifiable, Hashable {
    let appid: Int
    let name: String
    let shortDescription: String
    let currentPrice: Decimal?
    let originalPrice: Decimal?
    let discountPercent: Int?
    let currency: String?
    let storeURL: URL
    let capsuleImageURL: URL?
    let sourceRank: Int?
    let lastSeenAt: Date

    var historicalLowPrice: Decimal?
    var nearHistoricalLow: Bool

    var id: Int { appid }

    static func placeholder(appid: Int, rank: Int?) -> GameSnapshot {
        GameSnapshot(
            appid: appid,
            name: "App \(appid)",
            shortDescription: "暂无描述",
            currentPrice: nil,
            originalPrice: nil,
            discountPercent: nil,
            currency: nil,
            storeURL: URL(string: "https://store.steampowered.com/app/\(appid)")!,
            capsuleImageURL: nil,
            sourceRank: rank,
            lastSeenAt: Date(),
            historicalLowPrice: nil,
            nearHistoricalLow: false
        )
    }
}

struct HotGamesCachePayload: Codable {
    let updatedAt: Date
    let items: [GameSnapshot]
}
