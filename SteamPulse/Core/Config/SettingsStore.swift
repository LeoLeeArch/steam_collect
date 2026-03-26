import Foundation

final class SettingsStore {
    private let fileStore: FileStore
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    init(fileStore: FileStore) {
        self.fileStore = fileStore
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    }

    func load() -> AppSettings {
        do {
            try fileStore.ensureDirectories()
            let data = try fileStore.readData(at: fileStore.settingsFileURL)
            return try decoder.decode(AppSettings.self, from: data)
        } catch {
            let defaults = AppSettings.default
            try? save(defaults)
            return defaults
        }
    }

    func save(_ settings: AppSettings) throws {
        try fileStore.ensureDirectories()
        let data = try encoder.encode(settings)
        try fileStore.atomicWrite(data, to: fileStore.settingsFileURL)
    }
}
