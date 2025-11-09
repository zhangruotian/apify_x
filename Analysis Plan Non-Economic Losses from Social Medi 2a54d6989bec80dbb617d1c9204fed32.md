# Analysis Plan: Non-Economic Losses from Social Media

### Non-Economic Loss Classes

### 1) Displacement (forced relocation)

- **Definition**: People leave home due to flooding and stay elsewhere temporarily.
- **Count when**:
    - **Visual**: shelters (tents/school halls), group sleeping on mats, carrying large belongings during evacuation, boats moving household items.
    - **Text**: explicit “left home / in shelter / evacuated.”
- **Examples**: Gym floor lined with bedding; classroom converted to shelter.
- **Exclude**: Standing near home in water; generic street flooding without evidence of leaving home.

### 2) Education Disruption

- **Definition**: School closure or students unable to attend.
- **Count when**:
    - **Visual**: school building + “closed/suspended” sign; flooded gate/playground; students blocked at gate.
    - **Text**: explicit “school closed / can’t attend.”
- **Examples**: “Closed due to flood” at the gate; flooded classroom with floating desks.
- **Exclude**: Nearby road water only; no school/notice visible; vague “flood is severe.”

### 3) Health / Trauma

- **Definition**: Acute injuries, illness risks, or clear medical need.
- **Count when**:
    - **Visual**: bandages/bleeding, stretcher/first aid, skin infections/foot wounds, fall-injury in water.
    - **Text**: explicit “seeking treatment/pain/fever/infection.”
- **Examples**: Temporary medical post giving drugs; ambulance hindered by flood.
- **Exclude**: Just wading or “looks tired/sad” without health evidence.

### 4) Loss of Social Ties

- **Definition**: Disrupted connection to family/community and support networks.
- **Count when**:
    - **Visual**: community hubs destroyed; large cross-village relocation splitting households.
    - **Text**: explicit “lost contact / can’t return / community support gone.”
- **Examples**: Families scattered across different shelters; searching for missing relatives.
- **Exclude**: Pure landscapes/aerials with no social link; emotion only without “relationship break” info.

### 5) Cultural / Ritual Disruption

- **Definition**: Religious/festival/funeral rituals cancelled or altered.
- **Count when**:
    - **Visual**: flooded mosque/temple with halted ritual.
    - **Text**: explicit “prayer/festival/wedding/funeral postponed or cancelled.”
- **Examples**: Mosque hall inundated, prayers paused.
- **Exclude**: Flooded religious building without evidence of ritual disruption.

### 6) Caregiving Burden

- **Definition**: Marked increase in care difficulty for children/elderly/pregnant/disabled.
- **Count when**:
    - **Visual**: carrying infants/elderly through water, pushing wheelchair across flood, feeding/soothing infants in shelter queues.
    - **Text**: explicit “care difficulty / need help caring.”
- **Examples**: Volunteers lifting a bedridden elder; mother with infant in shelter line.
- **Exclude**: Presence of child/elder alone without a care-difficulty situation.

### 7) Water / Food Insecurity

- **Definition**: Access to safe water/food is obstructed or in shortage.
- **Count when**:
    - **Visual**: queues at water points with empty containers; distribution of food/bottled water; use of contaminated sources for drinking.
    - **Text**: explicit “lack water/food / need drinking water/food.”
- **Examples**: Relief site distributing bottled water; residents lining up with buckets.
- **Exclude**: Generic flooding/wading; inferential “flood ⇒ must lack water” without concrete cues.

### 8) Infrastructure Access (roads/clinics/schools)

- **Definition**: Inability to use roads/bridges/public services.
- **Count when**:
    - **Visual**: roads impassable; damaged/closed bridge; school/clinic “closed” notice; signs of power/water outage.
    - **Text**: explicit “road/bridge out; school/clinic closed.”
- **Examples**: Bus stopped at deep water; “temporarily closed” at school gate.
- **Exclude**: Water on street but vehicles still pass; no evidence of inaccessibility/closure.

### 9) Psychosocial Distress

- **Definition**: Pronounced fear, helplessness, grief, anger.
- **Count when**:
    - **Visual**: emotional expressions **with** clear hardship context (trapped, home damage, loss).
    - **Text**: explicit “afraid/hopeless/grieving/angry/anxious.”
- **Examples**: Family calling for help while stranded; speaking about losing home.
- **Exclude**: Music/filters creating mood; “looks unhappy” without hardship evidence.

## Analysis Methods

### Analysis 1: Frequency & Confidence (Which are more/less frequent?)

- **Metrics:**
    - **Occurrence Rate:** $p_k = \text{mean}(present_k)$
    - **Confidence-Weighted Rate:** $\tilde p_k = \frac{1}{N}\sum 1[present_k]\cdot conf_k$
    - **Mean Confidence when Present:** $\bar c_k = \text{mean}(conf_k \mid present_k)$
- **Chart:** Horizontal bar chart (juxtaposing $p_k$ and $\tilde {p_k}$), sorted by $\tilde {p_k}$.
- **Interpretation:** If a class has low $p_k$ and low $\bar c_k$, it suggests **weak social media visibility** or model difficulty.

### Analysis 2: Pairwise Co-occurrence

- **Metric:** Jaccard: $J_{ij}=\frac{\|L_i\cap L_j\|}{\|L_i\cup L_j\|}$
- **Chart:** 9x9 heatmap (upper triangle).
- **Interpretation:** e.g., High co-occurrence for `infrastructure_access` $\leftrightarrow$ `water_food_insecurity` suggests a mechanism ("access blocked $\rightarrow$ supply shortage").

### Analysis 3: Relationship with Water Depth / Urgency Score

- **Goal:** What hazard intensity causes what kind of non-economic loss?

### Analysis 4: Temporal Change

- **Metric:** $p_k(t)$ by week/day, smoothed (7-day moving average).
- **Chart:** Time-series line plot (9 facets).
- **Interpretation:** e.g., `infrastructure_access` peaks first; `education_disruption` / `caregiving` may **lag** (evidence for "dynamics" chapter).

#### Report Templates (Examples)

- **Overall Distribution:** "In social media posts, the most frequently observed non-economic losses were **infrastructure access** and **psychosocial distress**, with weighted occurrence rates of X% and Y%, respectively; **education disruption** and **caregiving burden** were less common (≤ Z%), suggesting **lower visibility** for these dimensions on social media."
- **Co-occurrence:** "`infrastructure_access` and `water_food_insecurity` showed high co-occurrence, supporting the 'access disruption and supply shortage' pathway; co-occurrence between `education_disruption` and `infrastructure_access` was also significant."
- **Relationship with intensity:** "As `water_depth_bin` increased, the occurrence of `infrastructure_access` rose monotonically; `psychosocial_distress` also showed an upward trend but with a gentler slope; `cultural_ritual_disruption` showed no significant trend with water depth."
- **Temporal Evolution:** "During the peak event week, `infrastructure_access` rates rose first; `education_disruption` peaked at +1 to +2 weeks, indicating a **lag**."

---

## Additional Analysis Dimensions

### Urgency Score

- Which visible cues (depth, crowd, damage, relief) are most correlated with urgency?
- Is there a threshold effect (e.g., a sharp jump from `knee` to `waist` depth)?

---

### Visual Cues

### a) water_depth_bin

- **Dose-Response Baseline:** Already used for losses and urgency.

### b) crowd_size_bin

- Does crowding co-occur with `infrastructure_access` (blocked roads) or `relief_visible`?

### c) relief_visible & relief_actor_type

- In what intensity/scenes does relief appear most?
- Do actor distributions (NGO/government/community) differ?
- Are NGOs  more concentrated in high-intensity/residential areas; government appears more in road/bridge scenarios?

### d) damage_signs

- **Question:** Structure and co-occurrence of facility damage (`road_blocked` vs `bridge_damage` vs `house_inundated`).
- **Conclusion example:** Road blockages and house inundation are highly co-occurrent; school/clinic closures show significant coupling with education/health losses.

---

### Demographic Presence

(children/elderly/pregnant/disabled_aid/male/female)

- Which groups have **low visibility**? In which scenes (`scene_type`/`context_area`)?
- Do certain losses correlate positively with specific group visibility (e.g., `caregiving` with children/elderly)?
- **Conclusion example:** Female and elderly are under-represented, particularly in aerial/roadway scenes; caregiving scenes increase child/elderly visibility.

---

### Scene Type

(aerial / ground_outdoor / indoor)

- **Visibility bias** of different scenes on loss detection.
- Do aerial views underestimate individual-level losses (e.g., `caregiving`, `health`)?

---

### Context Area

(settlement / farmland / roadway / riverbank / school_or_health_facility / mixed / unknown)

- Loss type in different area contexts.
- Are `displacement` or `water/food insecurity` more easily observed in riverbank/farmland?
- **Conclusion example:** "School/health contexts show higher rates of education disruption/health trauma; roadway contexts dominate infrastructure access disruptions."

---

### Sentiment

(fear/hopelessness/grief/anger/resilience/neutral/mixed)

- Relationship between emotion and **intensity**/loss/relief.
- Does relief co-occur with a rise in resilience or a drop in negative emotions?
- What emotions are most prevalent in social media posts?
- Which scenes/areas are more prone to certain emotional narratives?
- **Conclusion example:** "Fear/hopelessness rise with depth and infra disruptions; resilience is higher when relief is visible."

---

### Recovery

(recovery_signals, evidence)

- When did the recovery begin, and what was the intensity of the disaster at that time?

---

### Composite Indicators

- **NELI (Non-Economic Loss Intensity):**
    - Formula: $\sum_k w_k \cdot 1[present_k] \cdot conf_k$ (weights $w_k$ can be uniform or policy-driven).
    - Relation to  `urgency`, `depth`, `relief_visible`.
    - Compare NELI distribution by `scene`/`context`.
- **VISI (Visual Intensity):**
    - Formula: `depth_level_num + damage_signs_count + crowd_size_bin_num + relief_visible * α`
    - Relation to **NELI.**

---

## Data Quality & Validation

### To what extent can this data replace/supplement traditional media, surveys, etc.?

### Validation 1: Visual Verifiability

- +0.2 if `water_depth_bin` $\in$ {ankle, knee, waist, vehicle_height, indoor_flood}
- +0.2 if `damage_signs` $\in$ {road_blocked, house_inundated, bridge_damage, ...}
- +0.2 if any `loss_types.*.present=true` AND `confidence \geq 0.8`
- +0.2 if `scene_type` is `ground_outdoor` or `indoor` (0 for aerial)
- +0.2 if context_area $\neq$ "unknown"
    
    (Total 1.0, components adjustable)
    

### Validation 2: Caption-Image Consistency (CIC)

- Whether caption and image are consistent.

### Validation 3: Is the data reasonable?

- Do `loss_types` monotonically increase with `water_depth_bin` ?
- Is the expected **lag** present (e.g., `infrastructure_access` peaks before `education_disruption`)?
- Is the conditional probability $P(\text{education\_disruption} \mid \text{context=school})$ higher?
- Search for real news of the corresponding flood event. Does our social media data align with reports on severity, timing, and location (e.g., emotions, water depth, urgency)?
- Clustering on 0/1 vectors. Are the similar ones of same location?
- **`unknown`** Proportion:
    - Metric: % of `unknown` for `depth/area/scene`.
    - Use: As a "**visibility gap**" indicator.

---

## Stratified Analysis

### Platform Comparison (Twitter vs TikTok)

1. **Disaster Visibility**
    - Which platform surfaces flood impacts more clearly in posts (people, places, disruptions, and losses are easier to observe)?
2. **Women’s Visibility**
    - Which platform better represents women’s presence, voices, and situations in flood contexts?
3. **Emotion & Relief Narratives**
    - How do the platforms differ in emotional tone distributions (fear, grief, resilience, etc.) and in how often relief efforts appear?
4. **Caption–Image Consistency**
    - Which platform shows stronger alignment between what the caption says and what the image actually shows?
5. **Usefulness as Evidence**
    - Which platform’s content can more credibly complement or substitute traditional news, surveys, and official reports (for timeliness, specificity, and reliability)?

### Regional Comparison

1. **Differences Across Regions**
    - How do regions differ in non-economic losses, emotions, relief presence, demographics, scenes/contexts, and recovery signals?
2. **Visibility vs. Disaster Severity**
    - How does visibility align with independently known hazard intensity (e.g., region A higher category vs region B)?
    - Do higher-severity regions show clearer or earlier visibility of impacts, or are there mismatches?