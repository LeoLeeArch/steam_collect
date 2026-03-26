import Foundation

struct SteamChartsParser {
    func parseAppIDs(from html: String, source: HotSourceType, limit: Int) throws -> [HotEntry] {
        let regex = try NSRegularExpression(pattern: #"/app/(\d+)"#)
        let matches = regex.matches(in: html, range: NSRange(html.startIndex..<html.endIndex, in: html))

        var seen = Set<Int>()
        var entries: [HotEntry] = []

        for match in matches {
            guard match.numberOfRanges > 1,
                  let range = Range(match.range(at: 1), in: html),
                  let appid = Int(html[range])
            else {
                continue
            }

            if seen.contains(appid) { continue }
            seen.insert(appid)
            entries.append(HotEntry(appid: appid, rank: entries.count + 1, source: source))

            if entries.count >= limit {
                break
            }
        }

        return entries
    }
}
