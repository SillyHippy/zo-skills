---
name: process-server-locator
description: Find and locate process servers, skip tracers, and legal service professionals in a given city or county. Use when the user needs to find other process servers for overflow work, networking, or when a job is outside their service area. Also finds registered agents and business filing offices.
metadata:
  author: sillyhippy.zo.computer
  compatibility: "Created for Zo Computer"
---

# Process Server Locator

Find process servers, skip tracers, registered agents, and related legal service professionals in any US city or county.

## When To Use

- User has overflow work in another city/county
- User needs a local server for a distant jurisdiction
- User wants to network with other process servers
- User needs to find a registered agent for a business entity
- User asks "who serves in [city/county]?" or "find a process server in [location]"

## How to Search

### Google Maps Search (for local businesses)
```
maps_search: "process server in Tulsa OK"
maps_search: "private investigator in Oklahoma City OK"
maps_search: "registered agent services in [city, state]"
```

### Web Search (for associations and directories)
```
web_search: "National Association of Legal Process Servers directory [state]"
web_search: "[state] process server association members"
web_search: "NAPPS members [state]"
web_search: "process server directory [city] [state]"
```

### Web Research (for detailed results)
```
web_research: "certified process servers Oklahoma" — category: "company"
web_research: "NAPPS Next Day Rush Service providers" — include_text: ["NAPPS"]
```

## Key Organizations & Directories

- **NAPPS** (National Association of Professional Process Servers): https://www.napps.com/
- **NASP** (National Association of Skip Tracers and Process): https://www.skiptracers.org/
- **State associations**: Many states have their own process server associations
- **Better Business Bureau**: Often lists registered process servers
- **County clerk offices**: May maintain lists of registered process servers

## Oklahoma-Specific Resources

- **Oklahoma Process Server Association**: Search for state-specific groups
- **County Sheriff offices**: Some counties have approved server lists
- **Oklahoma Secretary of State**: For registered agent lookups: https://www.sos.ok.gov/

## Output Format

Always provide:
1. **Name** of server/company
2. **Location** (city, state)
3. **Contact info** (phone, website if available)
4. **Source** (where the info came from)
5. **Rating/reviews** if available from Maps

Example:
```
Process Servers in Tulsa, OK:

1. ABC Legal Service
   Phone: (918) 555-1234
   Website: abclegal.com
   Rating: 4.5/5 (Google Maps)
   Notes: Specializes in family law service

2. XYZ Process Serving
   Phone: (918) 555-5678
   Rating: 4.2/5 (Google Maps)
   Notes: NAPPS member, covers Tulsa County
```

## Never Hallucinate

- Only report servers that you actually find via search
- Do not invent phone numbers, names, or addresses
- If search returns no results, say so clearly
- Verify any contact information against at least one source
