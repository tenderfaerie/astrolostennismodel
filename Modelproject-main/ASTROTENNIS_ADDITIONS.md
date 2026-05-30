# AstroTennis Additions

This package contains the AstroTennis MVP built in this session.

## Included Features

- AstroTennis branding and browser metadata
- Tennis-ball sidebar icon
- SofaScore live tennis bridge using `tls_client`
- Live match list for ATP, WTA, Challenger, ITF Men, and ITF Women
- Live score and set-by-set display
- Current server indicator
- Live serve/stat grid:
  - Aces
  - Double faults
  - First serve
  - Second serve
  - First serve points won
  - Second serve points won
  - Service points won
  - Return points won
  - Break points saved
  - Break points converted / BPW
  - Winners
  - Unforced errors
  - Tiebreaks
- Point-by-point current-game panel
- Live moneyline display
- Projected winner strip
- Market win probability
- Astro model win probability
- 15-second live auto-refresh
- Sackmann CSV importer
- Local historical player database cache
- Player search and summary stats
- Prop analyzer MVP for pasted tennis lines

## Useful Commands

```bash
npm install
npm run import:sackmann
npm run dev -- -p 3000
npm run build
```

## Notes

The SofaScore integration is suitable for local prototyping. A production betting or analytics product should eventually use licensed data feeds for live scores, odds, and statistics.
