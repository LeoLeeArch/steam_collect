import Foundation

struct RefreshStatus: Codable {
    enum Outcome: String, Codable {
        case success
        case failed
    }

    let updatedAt: Date
    let outcome: Outcome
    let totalEntries: Int
    let succeededDetails: Int
    let failedDetails: Int
    let message: String
}

final class RefreshStatusStore {
    private let fileStore: FileStore
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let fm = FileManager.default

    init(fileStore: FileStore) {
        self.fileStore = fileStore
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    }

    private var stateDirectory: URL {
        fileStore.appSupportDirectory.appendingPathComponent("state", isDirectory: true)
    }

    private var refreshStatusURL: URL {
        stateDirectory.appendingPathComponent("refresh_status.json")
    }

    func save(_ status: RefreshStatus) {
        do {
            try fm.createDirectory(at: stateDirectory, withIntermediateDirectories: true)
            let data = try encoder.encode(status)
            try fileStore.atomicWrite(data, to: refreshStatusURL)
        } catch {
            // best-effort diagnostics path; avoid blocking refresh flow
        }
    }

    func load() -> RefreshStatus? {
        do {
            let data = try fileStore.readData(at: refreshStatusURL)
            return try decoder.decode(RefreshStatus.self, from: data)
        } catch {
            return nil
        }
    }
}
