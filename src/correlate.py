"""
Cross-domain correlation: the actual novel piece.

Combines on-chain bundle/sniper flags with social same-day/burst flags,
and checks whether the on-chain buy burst and the social shill burst
happened in the same window of time. That time-alignment is the signal no
existing tool (GoPlus, RugCheck, Bubblemaps) checks, because none of them
touch social data.

Scoring is intentionally simple and transparent (linear, capped 0-100) so
you can see exactly why a token got the score it got -- a black-box score
isn't useful for a validation prototype where the whole point is to
inspect *why* it flagged (or didn't flag) a known rug.
"""


def score_bundles(buyers, bundles):
    total = len(buyers) or 1
    largest = max((len(w) for w in bundles.values()), default=0)
    return round(min(100, (largest / total) * 100), 1), largest


def score_snipers(buyers, sniper_windows):
    total = len(buyers) or 1
    largest = max((w["count"] for w in sniper_windows), default=0)
    return round(min(100, (largest / total) * 100), 1), largest


def score_social(social_result):
    score = 0.0
    if social_result.get("same_day_clusters"):
        score += 30
    burst_windows = social_result.get("burst_windows", [])
    if burst_windows:
        largest = max(len(w["accounts"]) for w in burst_windows)
        total_posts = social_result.get("total_posts_analyzed", 1) or 1
        score += min(70, (largest / total_posts) * 100 * 2)
    return round(min(100, score), 1)


def find_overlap(sniper_windows, social_burst_windows, tolerance_seconds=600):
    """Check whether any on-chain sniper window overlaps any social burst window."""
    overlaps = []
    for sw in sniper_windows:
        for bw in social_burst_windows:
            latest_start = max(sw["start"], bw["start"] - tolerance_seconds)
            earliest_end = min(sw["end"], bw["end"] + tolerance_seconds)
            if latest_start <= earliest_end:
                overlaps.append({"onchain_window": sw, "social_window": bw})
    return overlaps


def build_report(buyers, bundles, sniper_windows, social_result):
    bundle_score, largest_bundle = score_bundles(buyers, bundles)
    sniper_score, largest_sniper = score_snipers(buyers, sniper_windows)
    social_score = score_social(social_result)
    overlaps = find_overlap(sniper_windows, social_result.get("burst_windows", []))
    overlap_bonus = 25 if overlaps else 0

    composite = round(
        min(100, 0.3 * bundle_score + 0.3 * sniper_score + 0.2 * social_score + overlap_bonus),
        1,
    )

    return {
        "composite_score": composite,
        "breakdown": {
            "bundle_score": bundle_score,
            "largest_bundle_size": largest_bundle,
            "sniper_score": sniper_score,
            "largest_sniper_window_size": largest_sniper,
            "social_score": social_score,
            "overlap_detected": bool(overlaps),
            "overlap_bonus_applied": overlap_bonus,
        },
        "detail": {
            "bundles": bundles,
            "sniper_windows": sniper_windows,
            "social_same_day_clusters": social_result.get("same_day_clusters"),
            "social_burst_windows": social_result.get("burst_windows"),
            "cross_domain_overlaps": overlaps,
        },
    }
