import SwiftUI

struct HotListView: View {
    @State var viewModel: HotListViewModel

    var body: some View {
        Group {
            switch viewModel.dataState {
            case .loading:
                LoadStatePanel(state: .loading, title: "", retryAction: nil)
            case .empty:
                LoadStatePanel(state: .empty, title: "暂无可展示数据", retryAction: {
                    Task { await viewModel.refresh() }
                })
            case .error(let message):
                LoadStatePanel(state: .error(message: message), title: "", retryAction: {
                    Task { await viewModel.refresh() }
                })
            case .success:
                List(viewModel.games) { game in
                    NavigationLink {
                        GameDetailView(game: game)
                    } label: {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("#\(game.sourceRank ?? 0)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                Text(game.name)
                                    .font(.headline)
                                Spacer(minLength: 8)
                                if game.nearHistoricalLow {
                                    ProductTag(type: .nearHistoricalLow)
                                }
                            }

                            HStack(spacing: 8) {
                                Text(PriceText.money(game.currentPrice, currency: game.currency))
                                Text("原价 \(PriceText.money(game.originalPrice, currency: game.currency))")
                                    .foregroundStyle(.secondary)
                                Text(PriceText.discount(game.discountPercent))
                                    .foregroundStyle(.green)
                            }
                            .font(.footnote)

                            Text("历史最低：\(PriceText.money(game.historicalLowPrice, currency: game.currency))")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
        }
        .navigationTitle("热门榜单")
        .safeAreaInset(edge: .top) {
            Text("提示：点任意游戏可进入详情页查看价格依据。")
                .font(.caption)
                .foregroundStyle(.secondary)
                .padding(.top, 4)
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("刷新") {
                    Task { await viewModel.refresh() }
                }
            }
        }
        .overlay {
            if viewModel.isLoading && !viewModel.games.isEmpty {
                ProgressView("刷新中...")
            }
        }
        .task {
            if viewModel.games.isEmpty { await viewModel.refresh() }
        }
        .safeAreaInset(edge: .bottom) {
            if let t = viewModel.lastUpdatedAt {
                Text("上次刷新：\(t.formatted())")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .padding(.bottom, 4)
            }
        }
    }
}
