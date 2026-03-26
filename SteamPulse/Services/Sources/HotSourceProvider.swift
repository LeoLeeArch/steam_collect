import Foundation

protocol HotSourceProvider {
    func fetchTopAppIDs(limit: Int, timeout: TimeInterval, retries: Int) async throws -> [HotEntry]
}

final class HotSourceService {
    private let providers: [HotSourceProvider]

    init(providers: [HotSourceProvider]) {
        self.providers = providers
    }

    func fetchAll(sources: [HotSourceType], limit: Int, timeout: TimeInterval, retries: Int) async throws -> [HotEntry] {
        var merged: [Int: HotEntry] = [:]

        for provider in providers {
            let entries = try await provider.fetchTopAppIDs(limit: limit, timeout: timeout, retries: retries)
            for entry in entries where sources.contains(entry.source) {
                if let old = merged[entry.appid], old.rank <= entry.rank { continue }
                merged[entry.appid] = entry
            }
        }

        return merged.values.sorted { $0.rank < $1.rank }
    }
}
