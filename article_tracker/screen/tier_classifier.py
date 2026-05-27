from __future__ import annotations

import logging
from typing import List

from article_tracker.models.article import Article, ScreeningTier
from article_tracker.models.profile import ResearchProfile
from article_tracker.screen.profile_loader import ProfileLoader

logger = logging.getLogger(__name__)


class TierClassifier:
    def __init__(self, profile: ResearchProfile, output_tiers: List[str] | None = None):
        self.profile = profile
        self.output_tiers = [ScreeningTier(t) for t in (output_tiers or ["core", "proxy", "eco"])]

    @classmethod
    def from_file(cls, path: str | None, output_tiers: List[str] | None = None) -> "TierClassifier":
        if path:
            profile = ProfileLoader.load(path)
            return cls(profile, output_tiers)
        return cls(ResearchProfile(
            core_keywords=["*"], proxy_keywords=[], eco_keywords=[], exclusion_keywords=[]
        ), output_tiers)

    @classmethod
    def from_config(cls, screening_config, output_tiers: List[str] | None = None) -> "TierClassifier":
        if screening_config.core_keywords:
            profile = ResearchProfile(
                core_keywords=screening_config.core_keywords or ["*"],
                proxy_keywords=screening_config.proxy_keywords or [],
                eco_keywords=screening_config.eco_keywords or [],
                exclusion_keywords=screening_config.exclusion_keywords or [],
                must_track_journals=screening_config.must_track_journals or [],
            )
            return cls(profile, output_tiers or screening_config.output_tiers)
        return cls.from_file(screening_config.profile_path, output_tiers or screening_config.output_tiers)

    def classify(self, articles: List[Article]) -> dict:
        stats = {"core": 0, "proxy": 0, "eco": 0, "noise": 0}
        for article in articles:
            tier, score = self._classify_one(article)
            article.screening_tier = tier
            article.relevance_score = score
            stats[tier.value] += 1
        return stats

    def filter_by_tiers(self, articles: List[Article]) -> List[Article]:
        return [a for a in articles if a.screening_tier in self.output_tiers]

    def _classify_one(self, article: Article) -> tuple[ScreeningTier, float]:
        text = f"{article.title} {article.abstract or ''}".lower()

        if self._matches_any(text, self.profile.exclusion_keywords):
            return ScreeningTier.noise, 0.0

        core_count = self._count_matches(text, self.profile.core_keywords)
        proxy_count = self._count_matches(text, self.profile.proxy_keywords)
        eco_count = self._count_matches(text, self.profile.eco_keywords)
        score = core_count * 3.0 + proxy_count * 2.0 + eco_count * 1.0

        if self.profile.must_track_journals and self._matches_journal(article):
            return ScreeningTier.core, max(score, 3.0)

        if core_count > 0:
            return ScreeningTier.core, score
        if proxy_count > 0:
            return ScreeningTier.proxy, score
        if eco_count > 0:
            return ScreeningTier.eco, score

        return ScreeningTier.noise, 0.0

    def _matches_any(self, text: str, keywords: List[str]) -> bool:
        for kw in keywords:
            if kw == "*":
                return True
            if kw.lower() in text:
                return True
        return False

    def _count_matches(self, text: str, keywords: List[str]) -> int:
        count = 0
        for kw in keywords:
            if kw == "*":
                count += 1
                continue
            if kw.lower() in text:
                count += 1
        return count

    def _matches_journal(self, article: Article) -> bool:
        venue = (article.venue or "").lower()
        for j in self.profile.must_track_journals:
            if j.lower() in venue:
                return True
        return False
