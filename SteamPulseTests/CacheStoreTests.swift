import XCTest
@testable import SteamPulse

final class CacheStoreTests: XCTestCase {
    func testLoadHotGamesWithMaxAge() throws {
        let fileStore = FileStore()
        let cache = CacheStore(fileStore: fileStore)

        let game = GameSnapshot.placeholder(appid: 123, rank: 1)
        try cache.saveHotGames([game])

        XCTAssertNotNil(cache.loadHotGames(maxAge: 60))
    }

    func testLoadHotGamesReturnsNilWhenCacheCorrupted() throws {
        let fileStore = FileStore()
        try fileStore.ensureDirectories()
        try Data("not-json".utf8).write(to: fileStore.hotGamesCacheURL, options: .atomic)

        let cache = CacheStore(fileStore: fileStore)
        XCTAssertNil(cache.loadHotGames())
    }
}
