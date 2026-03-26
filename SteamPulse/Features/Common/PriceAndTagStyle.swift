import SwiftUI

struct PriceText {
    static func money(_ value: Decimal?, currency: String?) -> String {
        guard let value else { return "--" }
        let code = (currency?.isEmpty == false ? currency! : "USD")
        let number = NSDecimalNumber(decimal: value)
        return "\(code) \(String(format: "%.2f", number.doubleValue))"
    }

    static func discount(_ value: Int?) -> String {
        guard let value else { return "--" }
        return "-\(value)%"
    }
}

enum ProductTagType {
    case freeCandidate
    case historicalLow
    case nearHistoricalLow

    var title: String {
        switch self {
        case .freeCandidate: return "免费候选"
        case .historicalLow: return "历史最低"
        case .nearHistoricalLow: return "接近史低"
        }
    }

    var tint: Color {
        switch self {
        case .freeCandidate: return .purple
        case .historicalLow: return .blue
        case .nearHistoricalLow: return .orange
        }
    }
}

struct ProductTag: View {
    let type: ProductTagType

    var body: some View {
        Text(type.title)
            .font(.caption2)
            .fontWeight(.semibold)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(type.tint.opacity(0.16), in: Capsule())
            .foregroundStyle(type.tint)
    }
}
