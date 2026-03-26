import Foundation
import Observation

@MainActor
@Observable
final class SettingsViewModel {
    var settings: AppSettings
    var saveMessage: String?

    private let settingsStore: SettingsStore

    init(settingsStore: SettingsStore) {
        self.settingsStore = settingsStore
        self.settings = settingsStore.load()
    }

    func save() {
        guard !settings.selectedSources.isEmpty else {
            saveMessage = "请至少选择一个数据源"
            return
        }

        do {
            try settingsStore.save(settings)
            saveMessage = "已保存"
        } catch {
            saveMessage = "保存失败：\(error.localizedDescription)"
        }
    }
}
