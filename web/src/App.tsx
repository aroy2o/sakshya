import { useState, type ReactNode } from 'react'
import { CommandStrip } from '@/components/beats/CommandStrip'
import { EvidenceBeat } from '@/components/beats/EvidenceBeat'
import { ImpactCurve } from '@/components/beats/ImpactCurve'
import { ModerationQueue } from '@/components/beats/ModerationQueue'
import { ReportAndMethods } from '@/components/beats/ReportAndMethods'
import { DistrictChoropleth } from '@/components/choropleth/DistrictChoropleth'
import { ErrorState } from '@/components/layout/ErrorState'
import { LoadingState } from '@/components/layout/LoadingState'
import { WatershedMap } from '@/components/map/WatershedMap'
import { BeatNav } from '@/components/shell/BeatNav'
import { GuidedTour } from '@/components/shell/GuidedTour'
import { CONFIGURED_MWS_ID } from '@/config'
import { useMwsList } from '@/hooks/useMwsList'
import { MapUiProvider } from '@/state/mapUiStore'

/**
 * Root layout: the 7-beat story (REAL_DATA_PLAN.md §7 / Reality Pass R6).
 * `activeBeat` picks which beat renders; `GuidedTour` (when open) drives
 * `activeBeat` itself via Next/Prev and exits cleanly back to plain
 * navigation, never leaving tour-only state behind. Watershed id comes
 * from `VITE_DEMO_MWS_ID` if set, else the first `GET /mws` result — never
 * hardcoded, per CLAUDE.md's "watershed choice is config, not code."
 */
function App() {
  const [activeBeat, setActiveBeat] = useState(1)
  const [tourOpen, setTourOpen] = useState(false)
  const mwsListQuery = useMwsList()

  const mwsId = CONFIGURED_MWS_ID ?? mwsListQuery.data?.[0]?.id

  let body: ReactNode
  if (mwsListQuery.isLoading) {
    body = <LoadingState label="Loading watersheds…" />
  } else if (mwsListQuery.isError) {
    body = <ErrorState message={(mwsListQuery.error as Error).message} onRetry={() => mwsListQuery.refetch()} />
  } else if (!mwsId) {
    body = <ErrorState message="No watersheds returned by GET /mws." />
  } else {
    switch (activeBeat) {
      case 1:
        body = <CommandStrip />
        break
      case 2:
        body = <DistrictChoropleth />
        break
      case 3:
        body = (
          <MapUiProvider>
            <WatershedMap mwsId={mwsId} />
          </MapUiProvider>
        )
        break
      case 4:
        body = <ImpactCurve mwsId={mwsId} />
        break
      case 5:
        body = <EvidenceBeat mwsId={mwsId} />
        break
      case 6:
        body = <ModerationQueue mwsId={mwsId} />
        break
      case 7:
        body = <ReportAndMethods mwsId={mwsId} />
        break
      default:
        body = null
    }
  }

  const isMapBeat = activeBeat === 2 || activeBeat === 3

  return (
    <div className="flex h-screen flex-col bg-(--bg) text-(--text)">
      <BeatNav active={activeBeat} onSelect={setActiveBeat} onStartTour={() => setTourOpen(true)} />
      <main className={`min-h-0 flex-1 ${isMapBeat ? '' : 'overflow-y-auto'}`}>{body}</main>
      {tourOpen && (
        <GuidedTour
          activeBeat={activeBeat}
          onGoTo={(id) => setActiveBeat(id)}
          onExit={() => setTourOpen(false)}
        />
      )}
    </div>
  )
}

export default App
