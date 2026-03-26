import Foundation

final class SteamChartsSourceProvider: HotSourceProvider {
    private let networkClient: NetworkClient
    private let parser = SteamChartsParser()

    init(networkClient: NetworkClient) {
        self.networkClient = networkClient
    }

    func fetchTopAppIDs(limit: Int, timeout: TimeInterval, retries: Int) async throws -> [HotEntry] {
        let sellersURL = URL(string: "https://store.steampowered.com/charts/topsellers")!
        let topPlayedURL = URL(string: "https://store.steampowered.com/charts/mostplayed")!

        async let sellersResult = fetchOne(url: sellersURL, source: .topSellers, limit: limit, timeout: timeout, retries: retries)
        async let playedResult = fetchOne(url: topPlayedURL, source: .topPlayed, limit: limit, timeout: timeout, retries: retries)

        let sellers = await sellersResult
        let played = await playedResult

        if sellers.isEmpty && played.isEmpty {
            throw URLError(.cannotLoadFromNetwork)
        }

        return sellers + played
    }

    private func fetchOne(url: URL, source: HotSourceType, limit: Int, timeout: TimeInterval, retries: Int) async -> [HotEntry] {
        do {
            let data = try await networkClient.get(url: url, timeout: timeout, retries: retries)
            let html = String(decoding: data, as: UTF8.self)
            return (try? parser.parseAppIDs(from: html, source: source, limit: limit)) ?? []
        } catch {
            return []
        }
    }
}
