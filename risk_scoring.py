"""
Multi-Factor Risk Scoring Engine
Calculates threat severity based on multiple indicators
"""

class RiskScorer:
    """Calculate composite risk scores from multiple factors"""
    
    def __init__(self):
        # High-risk keyword categories
        self.panic_keywords = {
            'extreme': ['death', 'kill', 'murder', 'terrorist', 'bomb', 'explosion', 'attack'],
            'high': ['urgent', 'breaking', 'alert', 'danger', 'threat', 'warning', 'emergency'],
            'medium': ['accident', 'fire', 'flood', 'earthquake', 'riot', 'protest'],
            'financial': ['scam', 'fraud', 'hack', 'leaked', 'crypto', 'free money', 'giveaway']
        }
        
        # Trusted domains for credibility
        self.trusted_domains = [
            'gov.in', 'pib.gov.in',
            'timesofindia.com', 'thehindu.com', 'indianexpress.com',
            'reuters.com', 'bbc.com', 'apnews.com',
            'news.ycombinator.com'
        ]
        
        # Spam indicators (low credibility)
        self.spam_indicators = [
            'blogspot', 'wordpress.com', 'bit.ly', 'tinyurl',
            'click', 'viral', 'shocking', 'download'
        ]
    
    def calculate_panic_score(self, title):
        """Analyze text for panic-inducing language. Returns: 0.0 to 1.0"""
        title_lower = title.lower()
        score = 0.0
        
        for severity, keywords in self.panic_keywords.items():
            for keyword in keywords:
                if keyword in title_lower:
                    if severity == 'extreme':
                        score += 0.4
                    elif severity == 'high':
                        score += 0.3
                    elif severity == 'medium':
                        score += 0.2
                    elif severity == 'financial':
                        score += 0.35
        
        if title.isupper() and len(title) > 10:
            score += 0.2
        
        if title.count('!') >= 2 or title.count('?') >= 2:
            score += 0.15
        
        sensational = ['shocking', 'unbelievable', 'incredible', 'must see', 'you wont believe']
        if any(word in title_lower for word in sensational):
            score += 0.1
        
        return min(score, 1.0)
    
    def calculate_credibility_score(self, platform, url):
        """Assess source credibility. Returns: 0.0 to 1.0 (higher = more credible)"""
        platform_credibility = {
            'Google News': 0.7,
            'Hacker News': 0.65,
            'YouTube': 0.4,
            'Google Trends': 0.5
        }
        
        base_cred = platform_credibility.get(platform, 0.5)
        
        if not url:
            return base_cred
        
        url_lower = url.lower()
        
        for domain in self.trusted_domains:
            if domain in url_lower:
                return min(base_cred + 0.3, 1.0)
        
        for indicator in self.spam_indicators:
            if indicator in url_lower:
                return max(base_cred - 0.3, 0.0)
        
        return base_cred
    
    def calculate_virality_score(self, views, virality_vd, hours_old=24):
        """Assess spread velocity. Returns: 0.0 to 1.0"""
        if views > 1000000:
            views_risk = 0.9
        elif views > 500000:
            views_risk = 0.7
        elif views > 100000:
            views_risk = 0.5
        elif views > 10000:
            views_risk = 0.3
        else:
            views_risk = 0.1
        
        if virality_vd > 10000:
            velocity_risk = 0.95
        elif virality_vd > 5000:
            velocity_risk = 0.8
        elif virality_vd > 1000:
            velocity_risk = 0.6
        elif virality_vd > 100:
            velocity_risk = 0.4
        else:
            velocity_risk = 0.2
        
        virality_risk = (views_risk * 0.3 + velocity_risk * 0.7)
        return min(virality_risk, 1.0)
    
    def calculate_keyword_score(self, title, tags):
        """Check for high-risk keywords (English + Hindi). Returns: 0.0 to 1.0"""
        combined_text = f"{title} {tags}".lower()
        
        try:
            from config import ALL_RISK_KEYWORDS
            risk_keywords = ALL_RISK_KEYWORDS
        except ImportError:
            risk_keywords = [
                'fake', 'scam', 'deepfake', 'leaked', 'hack',
                'terrorist', 'bomb', 'explosion', 'death',
                'urgent', 'breaking', 'alert'
            ]
        
        matches = 0
        for keyword in risk_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in combined_text or keyword in combined_text:
                matches += 1
        
        if matches >= 3:
            return 0.9
        elif matches == 2:
            return 0.6
        elif matches == 1:
            return 0.4
        else:
            return 0.1
    
    def calculate_composite_risk(self, title, platform, url, views, virality_vd, tags, ai_score, corroboration_score=None):
        """Combine all risk factors. Returns dict with composite_risk and individual scores.
           corroboration_score: 1.0 (True), 0.5 (Unverified), 0.0 (False/Debunked).
        """
        panic = self.calculate_panic_score(title)
        credibility = self.calculate_credibility_score(platform, url)
        virality = self.calculate_virality_score(views, virality_vd)
        keywords = self.calculate_keyword_score(title, tags)
        
        # Base composite score
        composite = (
            panic * 0.25 +
            (1 - credibility) * 0.20 +
            virality * 0.20 +
            keywords * 0.15 +
            ai_score * 0.20
        )

        # Apply Fact Check multiplier if available
        if corroboration_score is not None:
            if corroboration_score == 0.0:
                # Highly likely to be fake/debunked
                composite = min(composite * 1.5, 1.0)
            elif corroboration_score == 1.0:
                # Highly likely to be true
                composite = composite * 0.5
        
        return {
            'composite_risk': min(composite, 1.0),
            'panic_score': panic,
            'credibility_score': credibility,
            'virality_score': virality,
            'keyword_score': keywords,
            'ai_score': ai_score,
            'corroboration_score': corroboration_score
        }
