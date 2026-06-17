# StayFrame Lead Table Schema

Canonical file:
`~/ventures/stayframe/leads/list/prospects-s6-100-apify-social.csv`

Do not use or recreate deleted superseded CSVs:
- `prospects-s6-100.csv`
- `prospects-s6-100-social-pass1.csv`
- `prospects-s6-100-social-pass2.csv`

## Core Fields

- `property_name`: lead/account name.
- `market`: `TH` or `AU`.
- `location`, `country`: geography.
- `segment`: `active_meta_advertiser`, `ota_dependent`, or `au_layer`.
- `source_seed`: how the lead was found.
- `estimated_keys`, `adr_band`, `ota_presence`: fit and economics clues.
- `official_site`, `instagram`, `facebook`: seed-level contact/social fields; may contain `unknown`.
- `meta_ad_status`: seed-level Meta Ad Library/adscan status.
- `contact_channel`: best known channel before Apify.
- `decision_maker`: currently mostly `unknown`; S7/S8 should enrich this.
- `verification_status`: `verified`, `needs_verify`, `out_of_icp`.
- `icp_status`: `in_icp`, `maybe_icp`, `out_of_icp`.
- `outreach_angle`: `videographer_replacement`, `occupancy_led`, `commission_led`,
  `commission_or_occupancy`, `warm_lane_or_spec`, `do_not_prioritize`.
- `notes`, `evidence_urls`: audit trail.

## Apify Fields

- `apify_instagram`, `apify_facebook`, `apify_tiktok`: website-linked social profiles.
- `apify_emails`, `apify_phones`: website-extracted contact info.
- `apify_instagram_followers`, `apify_facebook_followers`: public follower counts when returned.
- `apify_facebook_ad_status`: page ad status when returned.
- `apify_source_domain`, `apify_original_start_url`, `apify_run_ids`: enrichment provenance.
- `apify_social_status`: `found`, `no_official_site`, `no_social_found`, `not_completed`.

## S7 Priority Rule

Start with `verified + in_icp`, then `needs_verify + in_icp`.
Exclude `out_of_icp` unless Jono explicitly wants a benchmark or one-off pitch.

Default first-pass ranking:
1. T1: verified, in ICP, contactable, strong visual upside or active ad signal.
2. T2: in ICP but needs verification, or verified maybe-ICP with strong contact data.
3. Verify: plausible but missing website/contact/ownership clarity.
4. Bench: out-of-ICP brands, chains, large professional resorts, real estate listings.
