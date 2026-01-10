"""Backstory claim decomposition into atomic, testable claims."""

import re
import hashlib
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

CLAIM_CATEGORIES = {
    "early_life_event",
    "formative_experience",
    "belief_about_world",
    "fear_or_psychological_constraint",
    "motivation_or_ambition",
    "behavioral_tendency",
    "skill_or_capability",
    "moral_or_narrative_constraint",
}


@dataclass
class Claim:
    claim_id: str
    claim_type: str
    claim_text: str
    confidence: float
    core_trait: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BackstoryDecomposer:
    def __init__(self):
        self.high_confidence_patterns = [
            r'\balways\b', r'\bnever\b', r'\bcertainly\b', r'\bdefinitely\b',
            r'\babsolutely\b', r'\bwithout\s+doubt\b', r'\bundoubtedly\b',
            r'\binevitably\b', r'\binvariably\b', r'\bconstantly\b',
            r'\bwill\s+always\b', r'\bwill\s+never\b', r'\bcompletely\b',
            r'\bentirely\b', r'\btotally\b', r'\bpermanently\b'
        ]
        
        self.low_confidence_patterns = [
            r'\bmaybe\b', r'\bperhaps\b', r'\bpossibly\b', r'\bprobably\b',
            r'\bmight\b', r'\bcould\b', r'\bseems?\b', r'\bappears?\b',
            r'\bsomewhat\b', r'\boccasionally\b', r'\bsometimes\b',
            r'\btends?\s+to\b', r'\blikely\b', r'\bsuggests?\b',
            r'\bimplies?\b', r'\bpotentially\b', r'\bpresumably\b'
        ]
        
        self.core_trait_patterns = [
            r'\bdefining\b', r'\bcore\b', r'\bfundamental\b', r'\bessential\b',
            r'\bcentral\s+to\b', r'\bshaped\s+by\b', r'\bdriven\s+by\b',
            r'\bforever\s+changed\b', r'\bwho\s+they\s+are\b', r'\bidentity\b'
        ]

    def _generate_claim_id(self, claim_text: str, index: int) -> str:
        content = f"{claim_text}_{index}"
        hash_digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
        return f"claim_{hash_digest[:12]}"

    def _calculate_confidence(self, text: str) -> float:
        text_lower = text.lower()
        
        high_count = sum(1 for pattern in self.high_confidence_patterns 
                        if re.search(pattern, text_lower))
        low_count = sum(1 for pattern in self.low_confidence_patterns 
                       if re.search(pattern, text_lower))
        
        base_confidence = 0.7
        confidence = base_confidence + (high_count * 0.1) - (low_count * 0.15)
        
        return max(0.0, min(1.0, confidence))

    def _is_core_trait(self, text: str) -> bool:
        text_lower = text.lower()
        
        for pattern in self.core_trait_patterns:
            if re.search(pattern, text_lower):
                return True
        
        strong_indicators = [
            r'\btrauma', r'\bdefining\s+moment\b', r'\blife-changing\b',
            r'\bprofound\b', r'\bdeep-seated\b', r'\bingrained\b'
        ]
        
        for pattern in strong_indicators:
            if re.search(pattern, text_lower):
                return True
                
        return False

    def _categorize_claim(self, claim_text: str) -> str:
        text_lower = claim_text.lower()
        
        category_patterns = {
            "early_life_event": [
                r'\bborn\b', r'\bchildhood\b', r'\byoung\b', r'\bgrowing\s+up\b',
                r'\bas\s+a\s+child\b', r'\bearly\s+years\b', r'\bfamily\b',
                r'\bparents?\b', r'\borphan\b', r'\bupbringing\b'
            ],
            "formative_experience": [
                r'\bexperienced\b', r'\bwitnessed\b', r'\bsurvived\b', r'\bendured\b',
                r'\bshaped\b', r'\bchanged\b', r'\blearned\b', r'\bdiscovered\b',
                r'\brealized\b', r'\btrauma\b', r'\bevent\b', r'\bmoment\b'
            ],
            "belief_about_world": [
                r'\bbelieves?\b', r'\bthinks?\b', r'\bviews?\b', r'\bsees?\s+the\s+world\b',
                r'\bconvinced\b', r'\bphilosophy\b', r'\bworldview\b', r'\bperspective\b',
                r'\btruth\b', r'\bprinciple\b'
            ],
            "fear_or_psychological_constraint": [
                r'\bfears?\b', r'\bafraid\b', r'\bterrified\b', r'\banxious\b',
                r'\bphobia\b', r'\bdreads?\b', r'\bhaunted\b', r'\btraumatized\b',
                r'\bcannot\b', r'\bunable\s+to\b', r'\bstruggles?\s+to\b'
            ],
            "motivation_or_ambition": [
                r'\bwants?\b', r'\bdesires?\b', r'\bseeks?\b', r'\bstrives?\b',
                r'\bgoal\b', r'\bambition\b', r'\bdream\b', r'\bhopes?\b',
                r'\baspires?\b', r'\bmotivated\b', r'\bdriven\s+to\b'
            ],
            "behavioral_tendency": [
                r'\btends?\s+to\b', r'\boften\b', r'\busually\b', r'\bhabit\b',
                r'\broutinely\b', r'\btypically\b', r'\bcharacteristically\b',
                r'\bprone\s+to\b', r'\binclined\s+to\b', r'\bbehavior\b'
            ],
            "skill_or_capability": [
                r'\bskilled\b', r'\btalented\b', r'\bexpert\b', r'\bproficient\b',
                r'\bability\b', r'\bcapable\b', r'\bcan\b', r'\bable\s+to\b',
                r'\bmastered\b', r'\btrained\b', r'\bknows?\s+how\b'
            ],
            "moral_or_narrative_constraint": [
                r'\bmust\b', r'\bshould\b', r'\bought\b', r'\bobligation\b',
                r'\bduty\b', r'\bresponsibility\b', r'\bcode\b', r'\bethics?\b',
                r'\bmorals?\b', r'\bvalues?\b', r'\bprinciples?\b', r'\bvow\b'
            ],
        }
        
        category_scores = {}
        for category, patterns in category_patterns.items():
            score = sum(1 for pattern in patterns if re.search(pattern, text_lower))
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        if any(word in text_lower for word in ['born', 'child', 'young']):
            return "early_life_event"
        elif any(word in text_lower for word in ['fear', 'afraid', 'cannot']):
            return "fear_or_psychological_constraint"
        elif any(word in text_lower for word in ['want', 'goal', 'seek']):
            return "motivation_or_ambition"
        else:
            return "formative_experience"

    def _split_compound_claims(self, text: str) -> List[str]:
        claims = []
        
        separators = [
            r',\s+and\s+',
            r',\s+but\s+',
            r';\s+',
            r'\.\s+',
        ]
        
        segments = [text]
        for separator in separators:
            new_segments = []
            for segment in segments:
                new_segments.extend(re.split(separator, segment))
            segments = new_segments
        
        for segment in segments:
            segment = segment.strip()
            if len(segment) > 10 and not segment.endswith(','):
                claims.append(segment)
        
        return claims if claims else [text]

    def decompose(self, backstory: str) -> List[Dict[str, Any]]:
        if not backstory or not backstory.strip():
            return []
        
        claims = []
        sentences = re.split(r'(?<=[.!?])\s+', backstory.strip())
        
        claim_index = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            atomic_claims = self._split_compound_claims(sentence)
            
            for claim_text in atomic_claims:
                claim_text = claim_text.strip()
                if not claim_text:
                    continue
                
                claim_id = self._generate_claim_id(claim_text, claim_index)
                claim_type = self._categorize_claim(claim_text)
                confidence = self._calculate_confidence(claim_text)
                core_trait = self._is_core_trait(claim_text)
                
                claim = Claim(
                    claim_id=claim_id,
                    claim_type=claim_type,
                    claim_text=claim_text,
                    confidence=confidence,
                    core_trait=core_trait
                )
                
                claims.append(claim.to_dict())
                claim_index += 1
        
        return claims


def decompose_backstory(backstory: str) -> List[Dict[str, Any]]:
    decomposer = BackstoryDecomposer()
    return decomposer.decompose(backstory)
