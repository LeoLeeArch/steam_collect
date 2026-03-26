import Foundation

actor RateLimiter {
    private var lastFireTime: Date?
    private let minInterval: TimeInterval

    init(minInterval: TimeInterval) {
        self.minInterval = max(0, minInterval)
    }

    func waitIfNeeded() async {
        guard let lastFireTime else {
            self.lastFireTime = Date()
            return
        }

        let elapsed = Date().timeIntervalSince(lastFireTime)
        let remaining = minInterval - elapsed
        if remaining > 0 {
            let nanos = UInt64(remaining * 1_000_000_000)
            try? await Task.sleep(nanoseconds: nanos)
        }
        self.lastFireTime = Date()
    }
}
