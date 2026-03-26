import Foundation

final class NetworkClient {
    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func get(url: URL, timeout: TimeInterval, retries: Int = 2) async throws -> Data {
        var attempt = 0
        var lastError: Error?

        while attempt <= retries {
            do {
                var request = URLRequest(url: url)
                request.timeoutInterval = timeout
                request.setValue("Mozilla/5.0 SteamPulse/1.0", forHTTPHeaderField: "User-Agent")

                let (data, response) = try await session.data(for: request)
                guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
                    throw URLError(.badServerResponse)
                }
                return data
            } catch {
                lastError = error
                attempt += 1
                if attempt <= retries {
                    let backoffNanos = UInt64(pow(2.0, Double(attempt - 1)) * 800_000_000)
                    try? await Task.sleep(nanoseconds: backoffNanos)
                }
            }
        }

        throw lastError ?? URLError(.unknown)
    }
}
