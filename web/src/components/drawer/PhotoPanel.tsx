import { SyntheticBadge } from '@/components/badges/SyntheticBadge'
import type { AssetDetail } from '@/types/domain'

export function PhotoPanel({ asset }: { asset: AssetDetail }) {
  const photos = [asset.photo1_url, asset.photo2_url].filter((url): url is string => url !== null)

  return (
    <section>
      <div className="mb-1.5 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-(--text)">Field photos</h3>
        <SyntheticBadge isSynthetic={asset.is_synthetic} photoSource={asset.photo_source} />
      </div>
      {photos.length === 0 ? (
        <p className="text-sm text-(--text-faint)">No photos submitted for this record.</p>
      ) : (
        <div className="grid grid-cols-2 gap-2">
          {photos.map((url, i) => (
            <img
              key={url}
              src={url}
              alt={`${asset.activity} — photo ${i + 1}`}
              className="aspect-square w-full rounded-md border border-(--border) object-cover"
            />
          ))}
        </div>
      )}
    </section>
  )
}
