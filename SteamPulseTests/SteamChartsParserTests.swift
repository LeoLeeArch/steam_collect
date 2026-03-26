import XCTest
@testable import SteamPulse

final class SteamChartsParserTests: XCTestCase {
    func testParseAppIDsDeduplicatesAndRespectsLimit() throws {
        let html = """
        <a href=\"/app/10\">A</a>
        <a href=\"/app/20\">B</a>
        <a href=\"/app/10\">A2</a>
        <a href=\"/app/30\">C</a>
        """

        let parser = SteamChartsParser()
        let result = try parser.parseAppIDs(from: html, source: .topSellers, limit: 2)

        XCTAssertEqual(result.count, 2)
        XCTAssertEqual(result[0].appid, 10)
        XCTAssertEqual(result[0].rank, 1)
        XCTAssertEqual(result[1].appid, 20)
        XCTAssertEqual(result[1].rank, 2)
    }
}
