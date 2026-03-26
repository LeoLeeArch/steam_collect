import SwiftUI

struct DiagnosticsView: View {
    @State private var cacheSummary: String = ""
    @State private var refreshSummary: String = ""
    @State private var state: PageDataState = .loading
    let cacheStore: CacheStore
    let refreshStatusStore: RefreshStatusStore

    var body: some View {
        List {
            Section("最近刷新") {
                if refreshSummary.isEmpty {
                    Text("暂无刷新记录")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                } else {
                    Text(refreshSummary)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }

            Section("缓存状态") {
                switch state {
                case .loading:
                    LoadStatePanel(state: .loading, title: "", retryAction: nil)
                case .empty:
                    LoadStatePanel(state: .empty, title: "暂无缓存数据", retryAction: {
                        refreshSummary()
                    })
                case .error(let message):
                    LoadStatePanel(state: .error(message: message), title: "", retryAction: {
                        refreshSummary()
                    })
                case .success:
                    Text(cacheSummary)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                    Button("刷新诊断信息") {
                        refreshSummary()
                    }
                }
            }

            Section("说明") {
                Text("当前版本未接入远程日志上传，仅展示本地可见状态。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("诊断")
        .task {
            refreshSummary()
        }
    }

    private func refreshSummary() {
        state = .loading
        if let latest = refreshStatusStore.load() {
            refreshSummary = """
            状态：\(latest.outcome == .success ? "成功" : "失败")
            时间：\(latest.updatedAt.formatted())
            详情成功：\(latest.succeededDetails)
            详情失败：\(latest.failedDetails)
            备注：\(latest.message)
            """
        } else {
            refreshSummary = ""
        }

        if let payload = cacheStore.loadHotGames() {
            cacheSummary = "缓存条目：\(payload.items.count)\n更新时间：\(payload.updatedAt.formatted())"
            state = .success
        } else {
            state = .empty
        }
    }
}
