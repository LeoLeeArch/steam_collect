import XCTest
@testable import SteamPulse

final class PageStateResolverTests: XCTestCase {
    func testLoadingState() {
        let state = PageStateResolver.resolve(isLoading: true, itemCount: 0, errorMessage: nil)
        if case .loading = state { } else { XCTFail("expected loading") }
    }

    func testErrorState() {
        let state = PageStateResolver.resolve(isLoading: false, itemCount: 0, errorMessage: "failed")
        if case .error(let message) = state {
            XCTAssertEqual(message, "failed")
        } else {
            XCTFail("expected error")
        }
    }

    func testEmptyState() {
        let state = PageStateResolver.resolve(isLoading: false, itemCount: 0, errorMessage: nil)
        if case .empty = state { } else { XCTFail("expected empty") }
    }

    func testSuccessState() {
        let state = PageStateResolver.resolve(isLoading: false, itemCount: 3, errorMessage: nil)
        if case .success = state { } else { XCTFail("expected success") }
    }
}
