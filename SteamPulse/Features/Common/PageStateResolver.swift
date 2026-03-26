import Foundation

struct PageStateResolver {
    static func resolve(isLoading: Bool, itemCount: Int, errorMessage: String?) -> PageDataState {
        if isLoading && itemCount == 0 { return .loading }
        if itemCount == 0, let errorMessage, !errorMessage.isEmpty { return .error(message: errorMessage) }
        if itemCount == 0 { return .empty }
        return .success
    }
}
