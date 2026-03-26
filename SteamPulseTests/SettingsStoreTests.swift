import XCTest
@testable import SteamPulse

final class SettingsStoreTests: XCTestCase {
    func testSettingsPersistAndReload() throws {
        let store = SettingsStore(fileStore: FileStore())
        var settings = AppSettings.default
        settings.topLimitPerSource = 55
        settings.notifyHistoricalLow = false
        settings.notifyNearHistoricalLow = true
        settings.selectedSources = [.topPlayed]

        try store.save(settings)
        let loaded = store.load()

        XCTAssertEqual(loaded.topLimitPerSource, 55)
        XCTAssertEqual(loaded.notifyHistoricalLow, false)
        XCTAssertEqual(loaded.notifyNearHistoricalLow, true)
        XCTAssertEqual(loaded.selectedSources, [.topPlayed])
    }
}
