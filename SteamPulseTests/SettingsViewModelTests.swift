import XCTest
@testable import SteamPulse

@MainActor
final class SettingsViewModelTests: XCTestCase {
    func testSaveBlockedWhenNoSourceSelected() {
        let vm = SettingsViewModel(settingsStore: SettingsStore(fileStore: FileStore()))
        vm.settings.selectedSources = []
        vm.save()
        XCTAssertEqual(vm.saveMessage, "请至少选择一个数据源")
    }
}
