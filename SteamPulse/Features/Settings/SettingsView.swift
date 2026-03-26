import SwiftUI

struct SettingsView: View {
    @State var viewModel: SettingsViewModel

    var body: some View {
        Form {
            Section("热门来源") {
                SourceToggleRow(title: "Top Sellers", source: .topSellers, selectedSources: $viewModel.settings.selectedSources)
                SourceToggleRow(title: "Top Played", source: .topPlayed, selectedSources: $viewModel.settings.selectedSources)
                Text("Top Sellers 偏向正在热卖，Top Played 偏向在线人数高。建议首次使用保持两者都开启。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Section("抓取策略") {
                Stepper("每源数量：\(viewModel.settings.topLimitPerSource)", value: $viewModel.settings.topLimitPerSource, in: 10...100, step: 5)
                Stepper("超时：\(Int(viewModel.settings.requestTimeoutSeconds)) 秒", value: $viewModel.settings.requestTimeoutSeconds, in: 5...30, step: 1)
                Stepper("重试次数：\(viewModel.settings.requestRetryCount)", value: $viewModel.settings.requestRetryCount, in: 0...5)
                Stepper("请求间隔：\(viewModel.settings.requestIntervalMilliseconds)ms", value: $viewModel.settings.requestIntervalMilliseconds, in: 100...1000, step: 50)
                Text("建议保持默认值：更稳定；提高数量会更全但刷新更慢。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Section("通知配置（预留）") {
                Toggle("史低提醒", isOn: $viewModel.settings.notifyHistoricalLow)
                Toggle("接近史低提醒", isOn: $viewModel.settings.notifyNearHistoricalLow)
                Text("当前版本尚未接入通知发送，仅保存配置；也不支持自动领取。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Section {
                Button("保存配置") {
                    viewModel.save()
                }
                Text("保存后回到首页或热门页，点击“刷新”即可按新配置拉取。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            if let message = viewModel.saveMessage {
                Section("状态") {
                    Text(message)
                }
            }
        }
        .navigationTitle("设置")
    }
}

private struct SourceToggleRow: View {
    let title: String
    let source: HotSourceType
    @Binding var selectedSources: [HotSourceType]

    var body: some View {
        Toggle(isOn: Binding(
            get: { selectedSources.contains(source) },
            set: { isOn in
                if isOn {
                    if !selectedSources.contains(source) { selectedSources.append(source) }
                } else {
                    selectedSources.removeAll { $0 == source }
                }
            }
        )) {
            Text(title)
        }
    }
}
