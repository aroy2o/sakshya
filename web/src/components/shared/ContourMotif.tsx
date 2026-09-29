/**
 * Quiet background texture for the two "hero" beats (Command strip, Impact
 * curve) — irregular nested contour rings, the actual visual language of a
 * watershed survey (a watershed IS a shape defined by elevation contours).
 * Drawn in the existing accent colour at very low opacity so it reads as
 * restraint, not a second competing hue (frontend-design skill: "spend
 * your boldness in one place").
 *
 * Static, no animation (skill: motion sparingly, only to draw attention —
 * a page-background texture isn't drawing attention to anything). Purely
 * decorative/non-data: `aria-hidden`, `pointer-events-none`.
 */
export function ContourMotif({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 1000 700"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 h-full w-full ${className ?? ''}`}
    >
      <g fill="none" stroke="var(--accent)" strokeWidth="1.1">
        <path
          d="M 860 90 C 760 40, 600 55, 520 120 C 430 195, 400 300, 440 400 C 480 500, 600 560, 720 540 C 850 515, 940 420, 945 300 C 950 190, 930 120, 860 90 Z"
          opacity="0.05"
        />
        <path
          d="M 830 130 C 745 90, 620 105, 555 160 C 475 225, 455 310, 490 390 C 525 470, 625 515, 725 500 C 830 483, 900 405, 905 310 C 908 220, 895 160, 830 130 Z"
          opacity="0.07"
        />
        <path
          d="M 800 170 C 730 140, 635 152, 585 195 C 520 248, 505 315, 533 380 C 562 445, 645 480, 725 468 C 810 455, 862 393, 866 315 C 869 245, 858 195, 800 170 Z"
          opacity="0.09"
        />
        <path
          d="M 770 205 C 715 182, 645 191, 608 224 C 558 267, 547 318, 568 368 C 590 418, 655 445, 718 436 C 785 426, 823 379, 826 318 C 828 265, 819 225, 770 205 Z"
          opacity="0.11"
        />
        <path
          d="M 742 238 C 700 220, 650 227, 622 252 C 585 285, 577 323, 593 361 C 610 399, 660 419, 709 412 C 761 404, 790 368, 792 322 C 794 282, 787 253, 742 238 Z"
          opacity="0.14"
        />
        <path
          d="M 715 268 C 685 255, 650 260, 630 278 C 605 301, 599 328, 610 354 C 622 380, 657 394, 692 389 C 729 383, 750 358, 752 325 C 753 297, 748 279, 715 268 Z"
          opacity="0.16"
        />
      </g>
    </svg>
  )
}
