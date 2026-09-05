# ServeTracker Beta Intake — VERIFY gate (copy/paste)

Use at end of every intake. If any box fails → not done.

## Environment
- [ ] Wrote to **BETA** `:3151` (or production only if Joseph said so)
- [ ] Did not mix beta test junk into production DB

## Packet
- [ ] Classification: Normal / ABC / Proof Serve handled correctly
- [ ] Case #, PBS, court caption, addresses extracted (not invented)

## Helcim
- [ ] Fee confirmed by Joseph
- [ ] INV # read back
- [ ] Amount matches
- [ ] Billing email correct
- [ ] Pay URL present (`just-legal-solutions.myhelcim.com/order/?token=`)

## ServeTracker
- [ ] Client searched before create; name non-empty
- [ ] Case searched before create
- [ ] `case_name` == Person Being Served
- [ ] `defendant_respondent` synced
- [ ] `court_name` = full caption (not county-only)
- [ ] `home_address` + `work_address` (Secondary) correct
- [ ] `documents_to_serve` has exact pleading titles when packet lists them
- [ ] `status` Open/active
- [ ] GET read-back matches POST

## Field sheet
- [ ] Generated; placeholders gone
- [ ] Notes/attempt log blank for handwriting
- [ ] PDF 1.4 normalized if WeasyPrint
- [ ] MEDIA path delivered (Telegram) when needed

## Drive
- [ ] Folder named by case #
- [ ] Parent = Site Upload `1ZB7XTSC_eD6m3F-6_yI2VP065cKEQzVq`
- [ ] Uploads via `google_api.py` only
- [ ] All files size > 0
- [ ] Folder listing confirms files

## Report
- [ ] Told Joseph what is done vs what still needs field work
- [ ] Did **not** claim complete without the above
