import Foundation

final class CacheStore {
    private let fileStore: FileStore
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    init(fileStore: FileStore) {
        self.fileStore = fileStore
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    }

    func saveHotGames(_ items: [GameSnapshot]) throws {
        try fileStore.ensureDirectories()
        let payload = HotGamesCachePayload(updatedAt: Date(), items: items)
        let data = try encoder.encode(payload)
        try fileStore.atomicWrite(data, to: fileStore.hotGamesCacheURL)
    }

    func loadHotGames() -> HotGamesCachePayload? {
        do {
            let data = try fileStore.readData(at: fileStore.hotGamesCacheURL)
            return try decoder.decode(HotGamesCachePayload.self, from: data)
        } catch {
            return nil
        }
    }

    func loadHotGames(maxAge: TimeInterval) -> HotGamesCachePayload? {
        guard let payload = loadHotGames() else { return nil }
        let age = Date().timeIntervalSince(payload.updatedAt)
        return age <= maxAge ? payload : nil
    }
}
