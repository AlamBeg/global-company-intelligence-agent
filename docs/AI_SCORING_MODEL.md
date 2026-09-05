# AI Scoring Model

## Design rule

Sentiment, impact, credibility, relevance, momentum, and risk are separate dimensions. A high-reach negative post should be negative because of its content, not because it has high reach.

## Discussion-level scores

### Relevance
How strongly the item concerns the target company/entity.

### Sentiment
Scaled from strongly negative through neutral to strongly positive, with confidence and aspect labels.

### Impact
Estimated importance based on available signals such as reach, engagement, author influence, source credibility, topic importance, velocity, originality, and propagation.

### Credibility
Quality of the source/author/evidence signals. This is not a factual truth score.

### Evidence confidence
Confidence that the evidence supports the associated analytical claim.

## Company-level sentiment

Company sentiment can be calculated from weighted discussion observations after deduplication. Weights should account for relevance, narrative independence, source quality, and configurable impact signals without allowing reach to change the underlying polarity.

Example presentation:

- Overall sentiment: 68/100
- Positive: 52%
- Neutral: 28%
- Negative: 20%
- Confidence: 0.87

These are example values only.

## Impact model

A configurable impact score may combine normalized components:

`impact = w1*reach + w2*engagement + w3*author_influence + w4*source_credibility + w5*topic_importance + w6*velocity + w7*propagation + w8*originality`

Weights and normalization versions must be stored.

## Topic momentum

Measure recent topic activity against a historical baseline using volume, unique sources, unique authors, velocity, and cross-platform propagation. A topic with low absolute volume can still be emerging if its growth rate is high, but the UI must show the baseline.

## Risk score

Risk should combine severity, momentum, evidence confidence, impact, affected audience, persistence, and corroboration. A risk score must not imply that an allegation is true.

## Calibration

Probabilistic outputs should be calibrated against labeled evaluation sets. Confidence must not simply equal model self-reported certainty.

## Versioning

Every score record must contain score_model_version, feature_version, taxonomy_version, and generated_at.

## Explainability

For material scores, expose contributing factors and representative evidence. Avoid opaque statements such as "AI says this is high risk" without supporting factors.
