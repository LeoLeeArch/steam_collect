import XCTest
@testable import SteamPulse

final class PriceHistoryStoreTests: XCTestCase {
    func testAppendIfNeededSkipsDuplicatePrice() throws {
        let store = PriceHistoryStore(fileStore: FileStore())
        let appid = Int.random(in: 900000...999999)

        var snapshot = GameSnapshot.placeholder(appid: appid, rank: 1)
        snapshot = GameSnapshot(
            appid: appid,
            name: "Test",
            shortDescription: "desc",
            currentPrice: 9.99,
            originalPrice: 19.99,
            discountPercent: 50,
            currency: "USD",
            storeURL: URL(string: "https://store.steampowered.com/app/\(appid)")!,
            capsuleImageURL: nil,
            sourceRank: 1,
            lastSeenAt: Date(),
            historicalLowPrice: nil,
            nearHistoricalLow: false
        )

        try store.appendIfNeeded(appid: appid, snapshot: snapshot)
        try store.appendIfNeeded(appid: appid, snapshot: snapshot)

        let history = try store.load(appid: appid)
        XCTAssertEqual(history.count, 1)
        XCTAssertEqual(history.first?.price, 9.99)
    }
}
