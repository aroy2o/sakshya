/** The 7-beat story, REAL_DATA_PLAN.md §7, verbatim order. */
export interface Beat {
  id: number
  slug: string
  title: string
  tourCaption: string
}

export const BEATS: Beat[] = [
  {
    id: 1,
    slug: 'command',
    title: 'Command strip',
    tourCaption: 'India-wide WDC-PMKSY numbers, then how the Northeast compares state by state.',
  },
  {
    id: 2,
    slug: 'district',
    title: 'Assam → Marigaon',
    tourCaption: 'Drill down from state to district: geotag coverage across all 51 real districts.',
  },
  {
    id: 3,
    slug: 'project',
    title: 'Project view',
    tourCaption: "Marigaon's real micro-watershed boundary, thematic layers, before/after satellite swipe.",
  },
  {
    id: 4,
    slug: 'impact',
    title: 'Impact curve',
    tourCaption: 'Treated vs. matched-control NDVI, 2016→2025, with the project-start marker and rainfall context.',
  },
  {
    id: 5,
    slug: 'evidence',
    title: 'Evidence drawer',
    tourCaption: 'One work, end to end: photos, integrity checklist, an advisory AI reading, the score breakdown.',
  },
  {
    id: 6,
    slug: 'moderation',
    title: 'Moderation queue',
    tourCaption: 'The real backlog: 51.2% of geotagged works are still waiting on a moderator.',
  },
  {
    id: 7,
    slug: 'report',
    title: 'Report & methods',
    tourCaption: 'Export what you just saw, and the methods/limits behind every number in it.',
  },
]
