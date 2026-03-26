import Foundation
import Observation

@MainActor
@Observable
final class DashboardViewModel {
    var isLoading = false
    var errorMessage: String?
    var games: [GameSnapshot] = []
    var lastUpdatedAt: Date?

    var dataState: PageDataState {
        PageStateResolver.resolve(isLoading: isLoading, itemCount: games.count, errorMessage: errorMessage)
    }

    private let refreshCoordinator: RefreshCoordinator

    init(refreshCoordinator: RefreshCoordinator) {
        self.refreshCoordinator = refreshCoordinator
        let cached = refreshCoordinator.loadCached()
        self.games = cached
        self.lastUpdatedAt = cached.first?.lastSeenAt
    }

    func refresh() async {
        isLoading = true
        defer { isLoading = false }

        do {
            games = try await refreshCoordinator.refresh()
            lastUpdatedAt = Date()
            errorMessage = nil
        } catch {
            errorMessage = "网络不可用或数据源暂时异常。"
            games = refreshCoordinator.loadCached()
        }
    }
}
