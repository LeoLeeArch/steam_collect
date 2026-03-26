import XCTest
@testable import SteamPulse

final class PriceAnalyzerTests: XCTestCase {
    func testHistoricalLowAndNearLowCalculation() {
        let analyzer = PriceAnalyzer()
        let history: [PriceHistoryPoint] = [
            .init(timestamp: Date(), price: 10, originalPrice: 20, discountPercent: 50, currency: "USD"),
            .init(timestamp: Date(), price: 8, originalPrice: 20, discountPercent: 60, currency: "USD")
        ]

        let resultNear = analyzer.analyze(currentPrice: 8.2, history: history, nearThreshold: 0.03)
        XCTAssertEqual(resultNear.historicalLow, 8)
        XCTAssertFalse(resultNear.nearHistoricalLow)
        XCTAssertTrue(resultNear.hasSufficientHistory)

        let resultAtLow = analyzer.analyze(currentPrice: 8, history: history, nearThreshold: 0.03)
        XCTAssertEqual(resultAtLow.historicalLow, 8)
        XCTAssertTrue(resultAtLow.nearHistoricalLow)
        XCTAssertTrue(resultAtLow.hasSufficientHistory)
    }

    func testNoHistoryDoesNotMarkNearLow() {
        let analyzer = PriceAnalyzer()
        let result = analyzer.analyze(currentPrice: 12.5, history: [])
        XCTAssertEqual(result.historicalLow, 12.5)
        XCTAssertFalse(result.nearHistoricalLow)
        XCTAssertFalse(result.hasSufficientHistory)
    }

    func testSingleHistoryPointDoesNotMarkNearLow() {
        let analyzer = PriceAnalyzer()
        let history: [PriceHistoryPoint] = [
            .init(timestamp: Date(), price: 10, originalPrice: 20, discountPercent: 50, currency: "USD")
        ]

        let result = analyzer.analyze(currentPrice: 10, history: history)
        XCTAssertEqual(result.historicalLow, 10)
        XCTAssertFalse(result.nearHistoricalLow)
        XCTAssertFalse(result.hasSufficientHistory)
    }

    func testNearLowThresholdBoundaryIsInclusive() {
        let analyzer = PriceAnalyzer()
        let history: [PriceHistoryPoint] = [
            .init(timestamp: Date(), price: 10, originalPrice: 20, discountPercent: 50, currency: "USD"),
            .init(timestamp: Date(), price: 8, originalPrice: 20, discountPercent: 60, currency: "USD")
        ]

        // 8 * 1.03 = 8.24, boundary should still be marked as near-low.
        let result = analyzer.analyze(currentPrice: 8.24, history: history, nearThreshold: 0.03)
        XCTAssertTrue(result.nearHistoricalLow)
    }
}
