import Foundation

struct FileStore {
    private let fm = FileManager.default

    func ensureDirectories() throws {
        try fm.createDirectory(at: settingsDirectory, withIntermediateDirectories: true)
        try fm.createDirectory(at: cacheDirectory, withIntermediateDirectories: true)
    }

    var settingsDirectory: URL {
        let docs = fm.urls(for: .documentDirectory, in: .userDomainMask).first!
        return docs.appendingPathComponent("config", isDirectory: true)
    }

    var settingsFileURL: URL {
        settingsDirectory.appendingPathComponent("settings.json")
    }

    var appSupportDirectory: URL {
        fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
    }

    var cacheDirectory: URL {
        appSupportDirectory.appendingPathComponent("cache", isDirectory: true)
    }

    var hotGamesCacheURL: URL {
        cacheDirectory.appendingPathComponent("hot_games.json")
    }

    func readData(at url: URL) throws -> Data {
        try Data(contentsOf: url)
    }

    func atomicWrite(_ data: Data, to url: URL) throws {
        let tmp = url.appendingPathExtension("tmp")
        try data.write(to: tmp, options: .atomic)
        if fm.fileExists(atPath: url.path) {
            try fm.removeItem(at: url)
        }
        try fm.moveItem(at: tmp, to: url)
    }
}
