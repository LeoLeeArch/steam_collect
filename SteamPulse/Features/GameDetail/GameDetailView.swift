import SwiftUI

struct GameDetailView: View {
    let game: GameSnapshot

    private var state: PageDataState {
        if game.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return .error(message: "游戏详情暂时不可用")
        }
        if game.currentPrice == nil && game.originalPrice == nil {
            return .empty
        }
        return .success
    }

    private var evidenceText: String {
        guard let current = game.currentPrice else {
            return "当前价格缺失，无法计算历史低价结论。"
        }

        if let low = game.historicalLowPrice {
            let currentText = PriceText.money(current, currency: game.currency)
            let lowText = PriceText.money(low, currency: game.currency)
            let nearLimit = low * Decimal(string: "1.03")!
            let nearLimitText = PriceText.money(nearLimit, currency: game.currency)
            return "当前价 \(currentText)，历史最低 \(lowText)。若当前价 ≤ \(nearLimitText) 则判定为“接近史低”（阈值 3%）。"
        }

        return "历史样本不足时，仅展示当前可得价格，不做“接近史低”判断。"
    }

    var body: some View {
        List {
            Section("游戏信息") {
                Text(game.name).font(.headline)
                Text(game.shortDescription.isEmpty ? "暂无简介" : game.shortDescription)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            Section("价格与优惠") {
                switch state {
                case .success:
                    LabeledContent("当前价", value: PriceText.money(game.currentPrice, currency: game.currency))
                    LabeledContent("原价", value: PriceText.money(game.originalPrice, currency: game.currency))
                    LabeledContent("折扣", value: PriceText.discount(game.discountPercent))
                    LabeledContent("历史最低", value: PriceText.money(game.historicalLowPrice, currency: game.currency))
                    LabeledContent("接近史低", value: game.nearHistoricalLow ? "是" : "否")

                    HStack(spacing: 8) {
                        if game.nearHistoricalLow {
                            ProductTag(type: .nearHistoricalLow)
                        }
                        if let low = game.historicalLowPrice,
                           let current = game.currentPrice,
                           current == low {
                            ProductTag(type: .historicalLow)
                        }
                    }
                case .empty:
                    LoadStatePanel(state: .empty, title: "暂无价格数据", retryAction: nil)
                case .error(let msg):
                    LoadStatePanel(state: .error(message: msg), title: "", retryAction: nil)
                case .loading:
                    LoadStatePanel(state: .loading, title: "", retryAction: nil)
                }
            }

            Section("判定依据") {
                Text(evidenceText)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Section("规则状态") {
                Text("免费候选规则当前为预留能力，尚未正式接入自动识别；本页结论目前仅基于价格历史分析。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Section("操作") {
                Link("打开 Steam 页面", destination: game.storeURL)
            }
        }
        .navigationTitle("游戏详情")
    }
}
