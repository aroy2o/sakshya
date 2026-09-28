import { useState } from 'react'
import { DistrictChoropleth } from '@/components/choropleth/DistrictChoropleth'
import { TopNav, type AppTab } from '@/components/layout/TopNav'
import { ErrorState } from '@/components/layout/ErrorState'
import { LoadingState } from '@/components/layout/LoadingState'
import { WatershedMap } from '@/components/map/WatershedMap'
import { CONFIGURED_MWS_ID } from '@/config'
import { useMwsList } from '@/hooks/useMwsList'
import { MapUiProvider } from '@/state/mapUiStore'

/**
 * Root layout: tab switch between the watershed map (FR5.1-FR5.4) and the
 * district choropleth (FR5.5). Picks the active watershed from
 * `VITE_DEMO_MWS_ID` if set, else the first `GET /mws` result — never a
 * hardcoded id, per CLAUDE.md's "watershed choice is config, not code."
 */
function App() {
  const [tab, setTab] = useState<AppTab>('map')
  const mwsListQuery = useMwsList()

  const mwsId = CONFIGURED_MWS_ID ?? mwsListQuery.data?.[0]?.id

  return (
    <div className="flex h-screen flex-col">
      <TopNav active={tab} onChange={setTab} />
      <main className="min-h-0 flex-1">
        {tab === 'map' &&
          (mwsListQuery.isLoading ? (
            <LoadingState label="Loading watersheds…" />
          ) : mwsListQuery.isError ? (
            <ErrorState message={(mwsListQuery.error as Error).message} onRetry={() => mwsListQuery.refetch()} />
          ) : mwsId ? (
            <MapUiProvider>
              <WatershedMap mwsId={mwsId} />
            </MapUiProvider>
          ) : (
            <ErrorState message="No watersheds returned by GET /mws." />
          ))}
        {tab === 'coverage' && <DistrictChoropleth />}
      </main>
    </div>
  )
}

export default App
