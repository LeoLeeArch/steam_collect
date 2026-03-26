import Foundation

struct GameDetailParser {
    func parse(data: Data, appid: Int, sourceRank: Int?) throws -> GameSnapshot? {
        let decoded = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard let appNode = decoded?["\(appid)"] as? [String: Any],
              let success = appNode["success"] as? Bool,
              success,
              let content = appNode["data"] as? [String: Any]
        else { return nil }

        let name = content["name"] as? String ?? "App \(appid)"
        let shortDescription = content["short_description"] as? String ?? ""
        let capsuleImageURL = (content["header_image"] as? String).flatMap(URL.init(string:))

        let priceOverview = content["price_overview"] as? [String: Any]
        let currency = priceOverview?["currency"] as? String
        let finalCents = priceOverview?["final"] as? Int
        let initialCents = priceOverview?["initial"] as? Int
        let discount = priceOverview?["discount_percent"] as? Int

        return GameSnapshot(
            appid: appid,
            name: name,
            shortDescription: shortDescription,
            currentPrice: finalCents.map { Decimal($0) / 100 },
            originalPrice: initialCents.map { Decimal($0) / 100 },
            discountPercent: discount,
            currency: currency,
            storeURL: URL(string: "https://store.steampowered.com/app/\(appid)")!,
            capsuleImageURL: capsuleImageURL,
            sourceRank: sourceRank,
            lastSeenAt: Date(),
            historicalLowPrice: nil,
            nearHistoricalLow: false
        )
    }
}
