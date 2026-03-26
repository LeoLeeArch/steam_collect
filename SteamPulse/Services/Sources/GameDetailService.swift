import Foundation

final class GameDetailService {
    private let networkClient: NetworkClient
    private let parser = GameDetailParser()

    init(networkClient: NetworkClient) {
        self.networkClient = networkClient
    }

    func fetchDetail(appid: Int, sourceRank: Int?, timeout: TimeInterval, retries: Int) async -> GameSnapshot {
        let url = URL(string: "https://store.steampowered.com/api/appdetails?appids=\(appid)&l=schinese&cc=us")!

        do {
            let data = try await networkClient.get(url: url, timeout: timeout, retries: retries)
            if let snapshot = try parser.parse(data: data, appid: appid, sourceRank: sourceRank) {
                return snapshot
            }
        } catch {
            // degrade to placeholder below
        }

        return GameSnapshot.placeholder(appid: appid, rank: sourceRank)
    }
}
