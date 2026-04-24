from __future__ import annotations

from models.fan import FanProfile


def calculate_score(profile: FanProfile) -> int:
    recency_bonus = 50
    cross_platform_bonus = 100 if profile.cross_platform or len(profile.platforms) > 1 else 0
    reach_score = min(profile.follower_count / 100, 200)
    score = (
        profile.comment_count * 30
        + profile.reply_count * 20
        + reach_score
        + cross_platform_bonus
        + recency_bonus
    )
    return int(round(score))


def build_reason(profile: FanProfile) -> str:
    parts: list[str] = []
    if profile.reply_count:
        parts.append(f"{profile.reply_count} direct replies")
    if profile.comment_count:
        parts.append(f"{profile.comment_count} comments")
    if profile.cross_platform or len(profile.platforms) > 1:
        parts.append("cross-platform engagement")
    if profile.follower_count:
        parts.append(f"{profile.follower_count:,} follower reach")
    return ", ".join(parts) if parts else "Visible repeated engagement"


def score_profile(profile: FanProfile) -> FanProfile:
    profile.cross_platform = profile.cross_platform or len(profile.platforms) > 1
    profile.score = calculate_score(profile)
    if not profile.reason:
        profile.reason = build_reason(profile)
    return profile
