import Foundation

final class PriceHistoryStore {
    private let fileStore: FileStore
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let fm = FileManager.default

    init(fileStore: FileStore) {
        self.fileStore = fileStore
    }

    private var historyDirectory: URL {
        fileStore.appSupportDirectory.appendingPathComponent("history", isDirectory: true)
    }

    func historyFileURL(for appid: Int) -> URL {
        historyDirectory.appendingPathComponent("\(appid).jsonl")
    }

    func appendIfNeeded(appid: Int, snapshot: GameSnapshot) throws {
        guard let price = snapshot.currentPrice, let currency = snapshot.currency else { return }

        try fm.createDirectory(at: historyDirectory, withIntermediateDirectories: true)
        let url = historyFileURL(for: appid)

        let newPoint = PriceHistoryPoint(
            timestamp: Date(),
            price: price,
            originalPrice: snapshot.originalPrice,
            discountPercent: snapshot.discountPercent,
            currency: currency
        )

        let existing = (try? load(appid: appid)) ?? []
        if let last = existing.last,
           last.price == newPoint.price,
           last.currency == newPoint.currency,
           last.discountPercent == newPoint.discountPercent {
            return
        }

        let data = try encoder.encode(newPoint)
        if fm.fileExists(atPath: url.path) {
            let handle = try FileHandle(forWritingTo: url)
            defer { try? handle.close() }
            try handle.seekToEnd()
            handle.write(data)
            handle.write(Data("\n".utf8))
        } else {
            var blob = Data()
            blob.append(data)
            blob.append(Data("\n".utf8))
            try blob.write(to: url, options: .atomic)
        }
    }

    func load(appid: Int) throws -> [PriceHistoryPoint] {
        let url = historyFileURL(for: appid)
        guard fm.fileExists(atPath: url.path) else { return [] }

        let data = try Data(contentsOf: url)
        guard let content = String(data: data, encoding: .utf8) else { return [] }
        return content
            .split(separator: "\n")
            .compactMap { line in
                try? decoder.decode(PriceHistoryPoint.self, from: Data(line.utf8))
            }
    }
}
