import SwiftUI

struct DashboardView: View {
    @State var viewModel: DashboardViewModel

    var body: some View {
        List {
            Section("首次使用说明") {
                Text("SteamPulse 会追踪热门游戏价格，帮助你发现“历史最低”和“接近史低”的机会。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                Text("手动刷新：右上角“刷新”按钮。首次打开会自动拉取一次数据。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Section("3 分钟演示路径") {
                Text("首页看说明 → 切到“热门榜单” → 点一款游戏进详情 → 到“设置”修改参数并保存 → 回到首页点击刷新。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Section("标签说明") {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 8) {
                        ProductTag(type: .freeCandidate)
                        Text("免费候选（规则待接入）")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                    HStack(spacing: 8) {
                        ProductTag(type: .historicalLow)
                        Text("当前价等于历史最低价")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                    HStack(spacing: 8) {
                        ProductTag(type: .nearHistoricalLow)
                        Text("当前价 ≤ 历史最低价上浮 3%")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Section("热门游戏") {
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
                    ForEach(viewModel.games.prefix(10)) { game in
                        NavigationLink {
                            GameDetailView(game: game)
                        } label: {
                            VStack(alignment: .leading, spacing: 8) {
                                Text(game.name).font(.headline)
                                Text(game.shortDescription)
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(2)

                                HStack(spacing: 8) {
                                    Text(PriceText.money(game.currentPrice, currency: game.currency))
                                        .font(.subheadline)
                                        .fontWeight(.semibold)
                                    if let discount = game.discountPercent {
                                        Text(PriceText.discount(discount))
                                            .font(.caption)
                                            .foregroundStyle(.green)
                                    }
                                    if game.nearHistoricalLow {
                                        ProductTag(type: .nearHistoricalLow)
                                    }
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            }
        }
        .navigationTitle("首页")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                if viewModel.isLoading {
                    ProgressView()
                } else {
                    Button("刷新") {
                        Task { await viewModel.refresh() }
                    }
                }
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
