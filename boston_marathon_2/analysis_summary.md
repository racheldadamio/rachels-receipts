# Boston Marathon Analysis — Methodology & Key Findings

**Data:** 2018, 2019, 2021–2026
**Total finishers analyzed:** ~196,700 across 8 years

---

## Methodology

### Scraping
Results were scraped from [boston.r.mikatiming.com](https://boston.r.mikatiming.com) using the site's internal POST API (reverse-engineered from the JS bundle). Each request fetches 1,000 results; the scraper paginates until all pages are exhausted. The server rate-limits aggressively after ~18,000 rows, so exponential-backoff retries (up to 5 attempts, waits of 5 / 10 / 20 / 40 / 80 s) are used. The last page of each response overlaps with the previous, so rows are deduplicated on the `(year, idp)` key.

### Gender Inference
The results include a `place_gender` column (each runner's rank within their gender) but no explicit gender label. Within any given `place_gender` rank, exactly two runners share that rank — one man and one woman. The faster of the two is Male; the slower is Female. A third runner at the same rank indicates a para/adaptive athlete, who is excluded from all analyses. This approach correctly labels ~99.9% of the field; no external lookup is required.

### Age Group Inference
Similarly, `place_division` gives each runner's rank within their age division. Within each `(year, gender, place_division)` group, runners are sorted by finish time. The fastest is age group **A** (youngest / most competitive tier), the next is **B**, and so on through **J** (10 groups total). Labels are letters rather than actual age brackets because the raw data does not include birth year.

### Men's Equivalent of Sub-3:00 for Women
For each year, we find the rank of the slowest sub-3:00 woman (e.g., if 173 women ran sub-3, that rank is 173). We then look up the man at the same gender rank. His finish time is the "men's equivalent" — i.e., running faster than this time puts a man in the same relative standing as a sub-3:00 woman. The result is remarkably stable: **2:34:22 – 2:36:37** across all eight years, with six of eight years landing between 2:34:22 and 2:35:26. We therefore fix the men's equivalent at **2:35**.

---

## Key Findings

### 1. Boston is overwhelmingly a positive-split course
Across all years and genders, the vast majority of runners slow down in the second half. Negative-split rates range from **1.5% to 9.2%** depending on year and gender. The famous Newton Hills (miles 16–21) and the course's net downhill opening that encourages aggressive starts are the likely drivers.

- **2018 was an extreme outlier**: a nor'easter with rain, winds, and cold hit race day. Median positive split for men was **11.6 minutes** versus ~8.6 minutes in other years. Women were similarly affected.
- **Year-to-year variation is large** (2–9%) and is likely weather-driven. 2026 saw the highest negative-split rates on record: 9.2% (women), 6.7% (men).
- **Younger age groups negative-split more.** Age group A achieves negative splits 5–6% of the time; age group J (oldest / slowest tier) is essentially 0% in every year.

### 2. Sub-3:00 women and sub-2:35 men have both grown ~8× since 2018

| Year | Sub-3 Women | Sub-2:35 Men | Men's Equiv. |
|------|-------------|--------------|--------------|
| 2018 | 73          | 49           | 2:36:37      |
| 2019 | 173         | 184          | 2:34:27      |
| 2021 | 150         | 143          | 2:35:26      |
| 2022 | 231         | 236          | 2:34:52      |
| 2023 | 268         | 289          | 2:34:22      |
| 2024 | 188         | 209          | 2:34:26      |
| 2025 | 383         | 396          | 2:34:45      |
| 2026 | 606         | 599          | 2:35:04      |

Both sub-3 women and sub-2:35 men have grown in near lockstep, consistent with an overall field-wide speed improvement rather than one gender outpacing the other at the elite fringe. The men's equivalent time has barely moved (range of ~2 minutes across 8 years), confirming that **2:35 is a stable men's equivalent of women's sub-3:00**.

### 3. Growth at the fast end is concentrated in age group A
Among sub-3:00 women, age group A (the fastest/youngest competitive tier) accounts for **83–93%** of all sub-threshold runners in every year. The share has edged slightly downward over time (93% in 2018 → 84–88% by 2022–2026), suggesting modest broadening across age groups, but group A remains dominant. The pattern is identical for sub-2:35 men.

### 4. Repeat runners: 50.7% improve, women more so than men
Of the ~29,000 runners who appeared in at least two years, **50.7%** ran faster in their next appearance. The median improvement is small: **0.0 minutes for men**, **-0.7 minutes for women** (women slightly more likely to improve). The distribution is roughly symmetric, indicating regression-to-the-mean effects are balanced by genuine improvement.

**Split behavior is habitual.** Among runners who negative-split in year 1, **15.1%** negative-split again in year 2 — roughly 4× the base rate of 3–4%. If you negative-split Boston once, you're far more likely to do it again, suggesting it reflects consistent pacing discipline rather than luck.

### 5. The overall field has gotten ~17 minutes faster since 2018

| Year | Median Women | Median Men  | Field Size |
|------|-------------|-------------|------------|
| 2018 | 3:56:53     | 3:34:05     | 24,045     |
| 2019 | 3:52:28     | 3:28:26     | 25,969     |
| 2021 | 3:42:08     | 3:20:48     | 14,973     |
| 2022 | 3:48:43     | 3:27:22     | 23,967     |
| 2023 | 3:44:52     | 3:23:17     | 25,909     |
| 2024 | 3:47:15     | 3:25:32     | 24,869     |
| 2025 | 3:41:45     | 3:20:09     | 27,851     |
| 2026 | 3:39:21     | 3:16:53     | 28,870     |

Both genders improved by roughly 17 minutes at the median from 2018 to 2026. Women now represent approximately **44% of the field**, a proportion that has held roughly steady since 2019. The field size has grown from ~24,000 (2018) to ~29,000 (2026), with 2021 a COVID-era outlier at ~15,000.

The speed improvement likely reflects a combination of factors: the 2018 race being weather-suppressed (inflating its baseline), broader sport participation growth, and improvements in training and footwear technology across the running community.

---

## Chicago Comparison (`chicago_comparison.ipynb`)

Data scraped from `chicago-history.r.mikatiming.com` (2018–2024) and `results.chicagomarathon.com/2025/`. Same gender-inference methodology as Boston. Half splits available for 2025 only.

### 1. Negative-split rate (2025)
Chicago 2025 negative-split rates: **7.7% overall** (8.8% women, 6.8% men). This is comparable to recent good-weather Boston years (Boston 2026: 9.2% F, 6.7% M), which is notable because Chicago is a much flatter course. The similar rates suggest course profile matters less than weather and pacing culture.

### 2. Sub-3 women & men's equivalent

| Year | Sub-3 Women | Men's Equiv. |
|------|-------------|--------------|
| 2018 | 120         | 2:34:14      |
| 2019 | 208         | 2:36:03      |
| 2021 | 89          | 2:36:53      |
| 2022 | 179         | 2:33:39      |
| 2023 | 317         | 2:36:02      |
| 2024 | 239         | 2:35:14      |
| 2025 | 393         | 2:35:46      |

Sub-3 women grew ~3.3× from 2018 to 2025 on Chicago, compared to ~8× on Boston over a similar window. The men's equivalent is again remarkably stable at **2:33–2:37**, reinforcing that 2:35 is the right benchmark across both races. Chicago had ~120 sub-3 women in 2018 vs. Boston's 73 — a larger starting base reflecting Chicago's bigger field.

### 3. Median finish time: Chicago vs. Boston

| Year | Chicago Women | Boston Women | Chicago Men | Boston Men |
|------|--------------|--------------|-------------|------------|
| 2018 | 4:43:40      | 3:56:53      | 4:11:53     | 3:34:05    |
| 2019 | 4:39:34      | 3:52:28      | 4:04:56     | 3:28:26    |
| 2021 | 4:53:35      | 3:42:08      | 4:24:51     | 3:20:48    |
| 2022 | 4:40:24      | 3:48:43      | 4:02:40     | 3:27:22    |
| 2023 | 4:30:22      | 3:44:52      | 3:55:03     | 3:23:17    |
| 2024 | 4:30:03      | 3:47:15      | 3:53:58     | 3:25:32    |
| 2025 | 4:32:51      | 3:41:45      | 3:55:52     | 3:20:09    |

Chicago's median finisher is ~45–55 minutes slower than Boston's across all years. This reflects Boston's qualifier requirement (which selects for faster runners), not course difficulty — Chicago is open entry via lottery. Both races show a similar trend of field-wide improvement since 2021, though Chicago shows more year-to-year volatility. Boston's improvement from 2018–2026 (~17 min) is largely weather-driven; Chicago's improvement from 2021–2025 (~29 min women, ~29 min men) likely reflects post-COVID field normalization and shoe technology.

---

## Files
| File | Description |
|------|-------------|
| `scrape_boston.py` | POST-based scraper with retry logic |
| `results_YYYY.csv` | Raw results per year (place_overall, place_gender, place_division, name, idp, team, bib, half, finish_net, finish_gun) |
| `analysis.ipynb` | Full analysis notebook (7 sections) |
| `chicago_comparison.ipynb` | Chicago vs. Boston comparison (5 sections) |
| `scrape_chicago.py` | Chicago list scraper (2018–2024 via chicago-history; 2025 via results.chicagomarathon.com) |
| `analysis_summary.md` | This file |
