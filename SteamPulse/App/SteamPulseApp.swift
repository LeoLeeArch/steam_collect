import SwiftUI

@main
struct SteamPulseApp: App {
    @State private var appContainer = AppContainer.bootstrap()

    var body: some Scene {
        WindowGroup {
            RootTabView(container: appContainer)
        }
    }
}
