import SwiftUI

struct RootTabView: View {
    let container: AppContainer

    var body: some View {
        TabView {
            NavigationStack {
                DashboardView(viewModel: DashboardViewModel(refreshCoordinator: container.refreshCoordinator))
            }
            .tabItem {
                Label("首页", systemImage: "house")
            }

            NavigationStack {
                HotListView(viewModel: HotListViewModel(refreshCoordinator: container.refreshCoordinator))
            }
            .tabItem {
                Label("热门", systemImage: "list.star")
            }

            NavigationStack {
                SettingsView(viewModel: SettingsViewModel(settingsStore: container.settingsStore))
            }
            .tabItem {
                Label("设置", systemImage: "gearshape")
            }

            NavigationStack {
                DiagnosticsView(cacheStore: container.cacheStore, refreshStatusStore: container.refreshStatusStore)
            }
            .tabItem {
                Label("诊断", systemImage: "stethoscope")
            }
        }
    }
}
