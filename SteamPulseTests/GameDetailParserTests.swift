import XCTest
@testable import SteamPulse

final class GameDetailParserTests: XCTestCase {
    func testParseSuccessWithPrice() throws {
        let parser = GameDetailParser()
        let data = """
        {
          \"100\": {
            \"success\": true,
            \"data\": {
              \"name\": \"Test Game\",
              \"short_description\": \"Desc\",
              \"header_image\": \"https://cdn.example.com/h.jpg\",
              \"price_overview\": {
                \"currency\": \"USD\",
                \"final\": 499,
                \"initial\": 1999,
                \"discount_percent\": 75
              }
            }
          }
        }
        """.data(using: .utf8)!

        let snapshot = try parser.parse(data: data, appid: 100, sourceRank: 1)
        XCTAssertEqual(snapshot?.name, "Test Game")
        XCTAssertEqual(snapshot?.currentPrice, 4.99)
        XCTAssertEqual(snapshot?.originalPrice, 19.99)
        XCTAssertEqual(snapshot?.discountPercent, 75)
    }

    func testParseReturnsNilWhenInvalid() throws {
        let parser = GameDetailParser()
        let data = """
        { \"100\": { \"success\": false } }
        """.data(using: .utf8)!

        let snapshot = try parser.parse(data: data, appid: 100, sourceRank: 1)
        XCTAssertNil(snapshot)
    }
}
