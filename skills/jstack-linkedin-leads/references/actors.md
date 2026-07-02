# HarvestAPI LinkedIn actors — full reference

Two pay-per-result Apify actors by `harvestapi`. No LinkedIn cookies/login needed.
Specs captured 2026-06-29 from the Apify API (actor details + build input schema + README).

Table of contents:
- [Actor 1 — linkedin-profile-search](#actor-1--linkedin-profile-search)
- [Actor 2 — linkedin-profile-posts](#actor-2--linkedin-profile-posts)
- [Pricing (both)](#pricing)
- [LinkedIn filter id lists](#linkedin-filter-id-lists)

---

## Actor 1 — linkedin-profile-search

- **Store:** `https://apify.com/harvestapi/linkedin-profile-search`
- **API slug (tilde form):** `harvestapi~linkedin-profile-search`
- **Purpose:** run a filtered LinkedIn people search, scrape the search result pages, and
  optionally open each profile for full detail; optionally enrich with a validated email.
- **Use for:** lead-gen lists by title/location/company/industry, recruiting/sourcing, market mapping.
- **Caps:** LinkedIn returns at most **2,500 profiles per query** and **100 search pages** (25/page).
  Use `autoQuerySegmentation` to exceed 2,500 across a broad query.

### Modes (`profileScraperMode`, default `Full`)
| Mode | What you get | Cost composition |
|------|--------------|------------------|
| `Short` | search-page data only (basic short profiles, 25/page) | $0.10 per search page |
| `Full` | Short + opens each profile for full detail | $0.10/page + $0.004 per full profile |
| `Full + email search` | Full + validated email lookup (SMTP-checked, not guaranteed) | $0.10/page + $0.01 per full profile |

### Input fields (no field is strictly required; supply `searchQuery` and/or filters)
| Field | Type | Notes |
|-------|------|-------|
| `profileScraperMode` | string enum | `Short` / `Full` / `Full + email search` (default `Full`) |
| `searchQuery` | string | fuzzy query, e.g. `Founder`, `Marketing Manager`; supports LinkedIn search operators |
| `maxItems` | int | cap total profiles across the whole run (0 = all up to 2,500/query) |
| `locations` | string[] | e.g. `United Kingdom` (use full country name; "UK" maps to Ukraine) |
| `currentCompanies` / `pastCompanies` | string[] | full LinkedIn company URLs |
| `schools` | string[] | e.g. `Stanford University` |
| `currentJobTitles` / `pastJobTitles` | string[] | e.g. `Software Engineer` |
| `industryIds` | string[] | numeric ids (see id lists below) |
| `seniorityLevelIds` | string[] | e.g. `120` = Senior |
| `functionIds` | string[] | e.g. `8` = Engineering |
| `yearsOfExperienceIds` | string[] | e.g. `3` = "3 to 5 years" |
| `yearsAtCurrentCompanyIds` | string[] | same scale as above |
| `companyHeadcount` | string[] | company size buckets |
| `companyHeadquarterLocations` | string[] | filter by employer HQ location |
| `profileLanguages` | string[] | profile language |
| `firstNames` / `lastNames` | string[] | prefer the `linkedin-profile-search-by-name` actor for name search |
| `recentlyChangedJobs` | bool | changed jobs in last 90 days |
| `recentlyPostedOnLinkedIn` | bool | posted in last 30 days |
| `exclude*` | string[] | `excludeLocations`, `excludeCurrentCompanies`, `excludePastCompanies`, `excludeSchools`, `excludeCurrentJobTitles`, `excludePastJobTitles`, `excludeIndustryIds`, `excludeSeniorityLevelIds`, `excludeFunctionIds`, `excludeCompanyHeadquarterLocations` |
| `startPage` | int | page to start from (default 1) |
| `takePages` | int | number of pages to scrape, 25 results each, max 100 |
| `autoQuerySegmentation` | bool | split a broad query into segments to beat the 2,500/query cap |
| `autoQuerySegmentationLevels` | string[] | which segmentation levels to use |
| `autoQuerySegmentationTargetCountries` | string[] | focus segmentation on these countries |
| `profileDeduplicationMode` | string enum | `off` / `insert_ids` / `insert_profiles` / `read_only` (needs MongoDB) |
| `mongoDbConnectionString` / `mongoDbDatabaseName` | string | for cross-run dedup |
| `postFilteringMongoDbQuery` | object | MongoDB query to refine results AFTER fetch (does not reduce cost) |
| `postFilteringMongoDbAggregation` | array | MongoDB aggregation pipeline, same caveat |

### Output — full profile (dataset item) top-level keys
`id`, `publicIdentifier`, `linkedinUrl`, `firstName`, `lastName`, `headline`,
`openToWork`, `hiring`, `premium`, `influencer`, `memorialized`,
`location{linkedinText, countryCode, parsed{country,state,city,...}}`, `objectUrn`,
`registeredAt`, `topSkills`, `connectionsCount`, `followerCount`, `verified`, `about`,
`currentPosition[]{companyName, companyLinkedinUrl, companyId, dateRange}`,
`profileTopEducation[]`, `profilePicture`, `coverPicture`, `photo`,
`experience[]`, `education[]`, `certifications[]`, `projects[]`, `volunteering[]`,
`receivedRecommendations[]`, `skills[]`, `publications[]`, `courses[]`, `patents[]`,
`honorsAndAwards[]`, `languages[]`, `causes[]`, `featured`, `composeOptionType`,
`moreProfiles[]` (related profiles surfaced on the page).
In **Full + email search** mode an `email` field is added when an address is found.
`Short` mode returns only the basic subset scraped from the search page.

Real sample: `references/sample_profile.json` (long arrays trimmed to 3 + `about` shortened).

---

## Actor 2 — linkedin-profile-posts

- **Store:** `https://apify.com/harvestapi/linkedin-profile-posts`
- **API slug (tilde form):** `harvestapi~linkedin-profile-posts`
- **Purpose:** collect posts published/reposted by a LinkedIn profile or company page (or a
  specific post/activity URL), with content, media, engagement, and optional reactions/comments.
- **Use for:** warming up outreach (cite a prospect's recent post), engagement analysis, content research.
- For searching posts by text/topic instead, use `harvestapi/linkedin-post-search`.

### Input fields (no field strictly required; `targetUrls` is the core input)
| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `targetUrls` | string[] | — | profile URLs (`/in/<slug>/`), company URLs (`/company/<slug>`), or specific post/activity URLs |
| `maxPosts` | int | 10 | per profile/company; `0` = all; overrides pagination |
| `postedLimit` | string enum | — | `any` / `1h` / `24h` / `week` / `month` / `3months` / `6months` / `year` |
| `postedLimitDate` | string | — | ISO date/timestamp; scrape from now back to this date |
| `includeQuotePosts` | bool | true | include shared posts with comments |
| `includeReposts` | bool | true | include shared posts without comments |
| `scrapeReactions` | bool | false | also scrape who reacted (charged per reaction) |
| `maxReactions` | int | 5 | per post |
| `postNestedReactions` | bool | false | nest reactions inside each post item |
| `scrapeComments` | bool | false | also scrape comments (charged per comment) |
| `maxComments` | int | 5 | per post |
| `commentsPostedLimit` | string enum | — | `any` / `1h` / `24h` / `week` / `month` |
| `postNestedComments` | bool | false | nest comments inside each post item |

### Output — post (dataset item) top-level keys
`type`, `id`, `linkedinUrl`, `content`,
`author{name, publicIdentifier, linkedinUrl, type, info, website, avatar}`,
`postedAt{timestamp, date, postedAgoShort, postedAgoText}`,
`postImages[]`, `document{title, transcribedDocumentUrl, coverPages[], totalPageCount}`,
`socialContent{shareUrl, ...visibility flags}`,
`engagement{likes, comments, shares, reactions[]{type, count}}`,
`reactions[]` (present when `scrapeReactions`; each `{id, reactionType, actor{name,linkedinUrl,position,...}, postId}`),
`comments[]` (present when `scrapeComments`).

Real sample: `references/sample_post.json` (reactions/comments trimmed to 2).

---

## Pricing

All prices are Apify-store list prices; HarvestAPI applies tiered discounts at SILVER/GOLD+ Apify plans.
Verify live in the actor's API response (`pricingInfos`) before any large run.

**linkedin-profile-search** (event-based; min charge $0.10/run):
- Search page (up to 25 short profiles): **$0.10** (SILVER $0.08, GOLD+ $0.05)
- Full profile: **$0.004** / profile = $4 per 1k (GOLD+ $0.0032)
- Full profile + email search: **$0.01** / profile = $10 per 1k (GOLD+ $0.008); not charged when a profile is too sparse to search

**linkedin-profile-posts** (event-based; min charge $0.002/run):
- Actor start: **$0.00005** (one-time)
- Post: **$0.002** / post = $2 per 1k (SILVER $0.00175, GOLD+ $0.0015)
- Reaction (only if `scrapeReactions`): **$0.002** each
- Comment (only if `scrapeComments`): **$0.002** each
- 0-result query: **$0.001**

Cost-control: pass `&maxTotalChargeUsd=<usd>` on the run URL (the script's `--max-charge`) as a hard cap,
and start with small `takePages` / `maxPosts` and `Short` mode to size a query cheaply.

## LinkedIn filter id lists
Industry ids (numeric): `https://github.com/HarvestAPI/linkedin-industry-codes-v2/blob/main/linkedin_industry_code_v2_all_eng_with_header.csv`
(e.g. `4` = Software Development, `43` = Financial Services). To discover seniority/function/location
ids, set the corresponding filter in LinkedIn's own people-search UI and read the id from the URL.
