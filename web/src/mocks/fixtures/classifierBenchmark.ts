/**
 * Mock for `GET /classifier/benchmark`, mirroring a real captured live
 * response (2026-09-28) verbatim — both models genuinely report
 * `accuracy_status: 'not_established'` right now; this is not a
 * mock-only stand-in value.
 */
import type { ClassifierBenchmark } from '@/types/domain'

export const classifierBenchmark: ClassifierBenchmark = {
  dataset: {
    n_photos: 45,
    source: 'Wikimedia Commons (individually hand-picked CC-licensed files, not a bulk crawl)',
    categories_covered: ['AM', 'BN', 'LH', 'LS', 'NC', 'PT', 'SM', 'VM'],
    categories_not_covered: ['OM'],
    includes_none_distractors: true,
    is_synthetic: false,
    methodology_doc: 'docs/CLASSIFIER_BENCHMARK.md',
    manifest_fields: [
      'id',
      'ground_truth_category',
      'commons_title',
      'file_page_url',
      'author',
      'license_short',
      'license_url',
      'retrieved_at',
    ],
  },
  models: [
    {
      model: 'llava',
      provider: 'ollama',
      n_photos: 9,
      n_correct: 1,
      n_errors: 0,
      accuracy: 0.1111,
      axis_labels: ['AM', 'VM', 'SM', 'PT', 'NC', 'BN', 'LS', 'LH', 'OM', 'UNKNOWN'],
      confusion_matrix: {
        SM: { UNKNOWN: 1 },
        PT: { UNKNOWN: 1 },
        BN: { UNKNOWN: 1 },
        AM: { UNKNOWN: 1 },
        VM: { UNKNOWN: 1 },
        LS: { UNKNOWN: 1 },
        LH: { UNKNOWN: 1 },
        NC: { UNKNOWN: 1 },
        UNKNOWN: { UNKNOWN: 1 },
      },
      generated_at: '2026-09-28T13:54:02.963279+00:00',
      note: "Measured on REAL Wikimedia Commons photos (scripts/real_photos/manifest.json), NOT the AI-generated synthetic set from generate_synthetic_photos.py/batch_classify.py. Do not present this figure interchangeably with synthetic-set accuracy. 6/9 responses failed structured-output validation and were degraded to an honest UNKNOWN/0.0-confidence result rather than a guessed category (services/vision_classifier.py's designed fallback) -- these are NOT the same as the model confidently looking and reporting it doesn't know.",
      n_schema_invalid_responses: 6,
      is_full_dataset: false,
      max_per_category: 1,
      neutral_declared_category: 'UNKNOWN',
      neutral_declared_activity: 'a general rural or agricultural scene',
      accuracy_status: 'not_established',
    },
    {
      model: 'moondream',
      provider: 'ollama',
      n_photos: 45,
      n_correct: 3,
      n_errors: 0,
      accuracy: 0.0667,
      axis_labels: ['AM', 'VM', 'SM', 'PT', 'NC', 'BN', 'LS', 'LH', 'OM', 'UNKNOWN'],
      confusion_matrix: {
        SM: { UNKNOWN: 10 },
        PT: { UNKNOWN: 6 },
        BN: { UNKNOWN: 5 },
        AM: { UNKNOWN: 5 },
        VM: { UNKNOWN: 3 },
        LS: { UNKNOWN: 3 },
        LH: { UNKNOWN: 5 },
        NC: { UNKNOWN: 5 },
        UNKNOWN: { UNKNOWN: 3 },
      },
      generated_at: '2026-09-28T13:22:08.816418+00:00',
      note: "Measured on REAL Wikimedia Commons photos (scripts/real_photos/manifest.json), NOT the AI-generated synthetic set from generate_synthetic_photos.py/batch_classify.py. Do not present this figure interchangeably with synthetic-set accuracy. 45/45 responses failed structured-output validation and were degraded to an honest UNKNOWN/0.0-confidence result rather than a guessed category (services/vision_classifier.py's designed fallback) -- these are NOT the same as the model confidently looking and reporting it doesn't know.",
      n_schema_invalid_responses: 45,
      is_full_dataset: true,
      max_per_category: null,
      neutral_declared_category: 'UNKNOWN',
      neutral_declared_activity: 'a general rural or agricultural scene',
      accuracy_status: 'not_established',
    },
  ],
  note: 'Accuracy figures here are measured on REAL Wikimedia Commons photos with hand-assigned ground truth, NOT on the AI-generated synthetic photo set used elsewhere in this project (scripts/generate_synthetic_photos.py / scripts/batch_classify.py). The two must never be presented interchangeably.',
}
