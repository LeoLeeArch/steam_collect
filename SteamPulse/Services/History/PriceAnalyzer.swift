import Foundation

struct PriceAnalysisResult {
    let historicalLow: Decimal?
    let nearHistoricalLow: Bool
    let hasSufficientHistory: Bool
}

struct PriceAnalyzer {
    func analyze(currentPrice: Decimal?, history: [PriceHistoryPoint], nearThreshold: Decimal = 0.03) -> PriceAnalysisResult {
        guard let currentPrice else {
            return PriceAnalysisResult(historicalLow: nil, nearHistoricalLow: false, hasSufficientHistory: false)
        }

        let lows = history.map(\.price)
        guard let historicalLow = lows.min() else {
            // 新游戏无历史，避免误判 near-low
            return PriceAnalysisResult(historicalLow: currentPrice, nearHistoricalLow: false, hasSufficientHistory: false)
        }

        // 历史样本不足（< 2）时仅报告样本内最低，不标记 near-low
        guard history.count >= 2 else {
            return PriceAnalysisResult(historicalLow: historicalLow, nearHistoricalLow: false, hasSufficientHistory: false)
        }

        let nearLimit = historicalLow * (1 + nearThreshold)
        return PriceAnalysisResult(
            historicalLow: historicalLow,
            nearHistoricalLow: currentPrice <= nearLimit,
            hasSufficientHistory: true
        )
    }
}
