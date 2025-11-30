# Non-Economic Losses Analysis - Walk-Through

**Data Source**: `merged_all_flood_data.csv` - Social media posts (Twitter + TikTok) with VLM-inferred fields  
**Analysis Goal**: Quantify and validate non-economic flood losses from social media imagery

---

## 1. Setup & Data Loading

**What**: Initialize libraries, define loss categories, load CSV  
**Key Constants**:
- 9 **Loss Types**: displacement, education_disruption, health_trauma, social_ties_loss, cultural_ritual_disruption, caregiving_burden, water_food_insecurity, infrastructure_access, psychosocial_distress
- Each has `_present` (bool) and `_confidence` (0-1) fields from VLM

**Results**: 2,964 posts loaded, 2,540 with valid timestamps

---

## 2. Non-Economic Loss (NEL) Definitions

**Concept**: 9 standardized loss categories based on visual + text evidence  
**Key Examples**:
- **Displacement**: shelters, evacuation scenes, carrying belongings
- **Infrastructure Access**: impassable roads, closed schools/clinics
- **Health/Trauma**: injuries, medical treatment, illness risk
- **Caregiving Burden**: carrying children/elderly through water, shelter care

**Purpose**: Ground truth definitions for VLM annotation quality assessment

---

## 3. NEL Frequency Analysis

**Metrics**:
- **Occurrence Rate** (p_k): % of posts showing loss k
- **Confidence-Weighted Rate** (p̃_k): weighted by VLM confidence
- **Mean Confidence** (c̄_k): average confidence when present

**Results** (Top 3):
1. **Infrastructure Access**: 53% occurrence, 87% confidence → Most visible
2. **Displacement**: 15% occurrence, 87% confidence → Moderately visible
3. **Psychosocial Distress**: 33% occurrence, 67% confidence → Lower confidence

**Interpretation**: Infrastructure disruptions are highly visible in social media; individual-level losses (caregiving, health, education) are under-captured.

---

## 4. NEL Co-occurrence Analysis

**Method**: Jaccard similarity matrix (9×9) - measures overlap between loss types  
**Formula**: J(i,j) = |L_i ∩ L_j| / |L_i ∪ L_j|

**Key Findings**:
- **Displacement ↔ Caregiving**: J=0.26 (strongest pair)  
  → Evacuation increases care difficulty
- **Displacement ↔ Infrastructure**: J=0.23  
  → Blocked roads trigger relocation
- **Health Hub**: Health/trauma co-occurs with social ties loss (0.17), caregiving (0.16), distress (0.13)

**Interpretation**: Reveals plausible causal pathways (mobility→relocation→care, health→social→emotion)

---

## 5. Dose-Response: Water Depth & Urgency

**Analysis**:
- **Dose-Response Curves**: NEL occurrence rate vs. water depth (none → ankle → knee → waist → vehicle-height)
- **Urgency Box Plot**: Urgency score distribution across depth levels

**Key Results**:
- **Infrastructure Access**: Monotonic increase with depth (tight CIs)
- **Displacement**: Peaks at knee-waist, drops at vehicle-height
- **Urgency-Depth Correlation**: ρ=0.53 (Spearman)  
  → Largest jump at **knee-level** (threshold effect: Δ=1.43)

**Interpretation**: Knee-depth is a practical "hazard salience" threshold; social media best captures infrastructure impacts, not individual losses.

---

## 6. Composite Indicators

**NELI (Non-Economic Loss Intensity)**: Sum of confidence scores across 9 loss types  
**VISI (Visual Intensity Score)**: depth_level + damage_signs + crowd_size + relief_visible

**Correlations** (Spearman):
- NELI ↔ VISI: ρ=0.76
- NELI ↔ Urgency: ρ=0.82
- VISI ↔ Urgency: ρ=0.80

**VISI-NELI Dose-Response**: Binning by VISI deciles → monotonic NELI increase (narrow CIs)

**Interpretation**: Visual hazard intensity robustly predicts verifiable non-economic losses.

---

## 7. Temporal Trends

**Method**: 3-day moving average of daily NELI and VISI (Bangladesh, Aug 19 – Sep 3, 2024)  
**Normalization**: Scale both to [0,1] for comparison

**Results**:
- Both rise during **extreme rainfall** (Aug 19–23)
- Peak around **Aug 28–29** (national impact peak)
- Remain elevated afterwards

**Interpretation**: Social posts are a **timely proxy** for NEL consequences, mirroring official disaster reports.

---

## 8. Urgency Drivers

**Analysis**: Spearman correlation of urgency score with visual cues

**Rankings**:
1. **Water Depth**: ρ=0.530 (dominant driver)
2. **Damage Signs**: ρ=0.413
3. **Crowd Size**: ρ=0.148
4. **Relief Visible**: ρ=0.021

**Threshold Effect**: Urgency mean jumps **1.43 points** from ankle→knee depth

**Interpretation**: Water depth is the primary urgency signal; knee-level is a critical visibility threshold.

---

## 9. Demographic Visibility

**Overall Rates**:
- Male: 50%, Female: 29%, Children: 19%
- Elderly: 4%, Disabled Aid: 0.2%, Pregnant: 0.1%

**Caregiving Effect** (visibility uplift when caregiving burden present):
- Children: +78%
- Female: +63%
- Elderly: +11%

**Interpretation**: Vulnerable groups are under-represented overall; caregiving scenes function as a "visibility gate" for dependents.

---

## 10. Sentiment Analysis

**Overall Prevalence**:
- Neutral: 34%, Fear: 15%, Resilience: 12%
- Grief: 8%, Hopelessness: 5%, Anger: 4%

**Relief Effect** (difference when relief visible):
- Resilience: +33%, Neutral: +11%
- Fear: -5%, Grief: -4%, Hopelessness: -3%

**Interpretation**: Aid imagery shifts framing from acute distress to recovery-oriented narratives.

---

## 11. Platform Comparison (Twitter vs. TikTok)

**Mean Scores**:
| Platform | Urgency | NELI | VISI |
|----------|---------|------|------|
| TikTok   | 2.31    | 0.89 | 4.49 |
| Twitter  | 1.33    | 0.72 | 3.37 |

**Demographic Visibility**:
- Twitter: Higher for children (21%), female (31%), elderly (5%)
- TikTok: Higher for male (52%)

**Interpretation**: TikTok shows higher visual intensity and urgency; Twitter better captures vulnerable groups. Likely **compositional differences** (content type, user behavior) rather than platform causality.

---

## Key Takeaways

1. **Visibility Bias**: Infrastructure disruptions dominate social media; individual losses (caregiving, health, education) are systematically under-captured
2. **Knee-Depth Threshold**: Critical salience point for urgency and NEL detection
3. **Composite Indicators Work**: NELI and VISI are robust, correlated proxies for flood impacts
4. **Temporal Validity**: Social media trends align with official disaster timelines
5. **Caregiving as Gateway**: Scenes with caregiving burden dramatically increase visibility of vulnerable demographics
6. **Platform Differences**: TikTok = higher intensity; Twitter = better demographic coverage

---

## Limitations & Next Steps

**Limitations**:
- VLM confidence varies by loss type (psychosocial distress = lower)
- Rare losses (cultural disruption, education) have sparse data
- Demographic under-representation (especially disabled, pregnant)

**Next Steps**:
- Cross-validate with ground surveys
- Refine VLM prompts for low-visibility categories
- Expand temporal analysis to multi-year datasets
- Test causal pathways (e.g., infrastructure → displacement)

