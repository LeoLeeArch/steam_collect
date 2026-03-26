import SwiftUI

enum PageDataState {
    case loading
    case empty
    case error(message: String)
    case success
}

struct LoadStatePanel: View {
    let state: PageDataState
    let title: String
    let retryAction: (() -> Void)?

    var body: some View {
        switch state {
        case .loading:
            VStack(spacing: 10) {
                ProgressView()
                Text("加载中...")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .center)
            .padding(.vertical, 18)

        case .empty:
            VStack(spacing: 8) {
                Text(title)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                if let retryAction {
                    Button("重试") { retryAction() }
                        .buttonStyle(.bordered)
                }
            }
            .frame(maxWidth: .infinity, alignment: .center)
            .padding(.vertical, 18)

        case .error(let message):
            VStack(spacing: 8) {
                Text("加载失败")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                Text(message)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                if let retryAction {
                    Button("重试") { retryAction() }
                        .buttonStyle(.borderedProminent)
                }
            }
            .frame(maxWidth: .infinity, alignment: .center)
            .padding(.vertical, 18)

        case .success:
            EmptyView()
        }
    }
}
