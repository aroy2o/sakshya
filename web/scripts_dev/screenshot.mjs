import puppeteer from 'puppeteer-core'

const BASE = 'http://localhost:5173'
const OUT_DIR = '/home/aroy2o/Music/SIH/sakshya/docs/screenshots'
const CHROME = '/usr/bin/google-chrome'

const beats = [
  { n: 1, slug: '01-command-strip' },
  { n: 2, slug: '02-district-drilldown' },
  { n: 3, slug: '03-project-view' },
  { n: 4, slug: '04-impact-curve' },
  { n: 5, slug: '05-evidence-drawer' },
  { n: 6, slug: '06-moderation-queue' },
  { n: 7, slug: '07-report-methods' },
]

async function main() {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--use-gl=angle',
      '--use-angle=swiftshader-webgl',
      '--enable-unsafe-swiftshader',
      '--enable-webgl',
      '--enable-webgl2',
      '--ignore-gpu-blocklist',
    ],
  })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  page.on('console', (msg) => {
    if (msg.type() === 'error') console.log('[console.error]', msg.text())
  })
  page.on('pageerror', (err) => console.log('[pageerror]', err.message))

  await page.goto(BASE, { waitUntil: 'networkidle0', timeout: 30000 })
  await new Promise((r) => setTimeout(r, 1500))

  for (const beat of beats) {
    const buttons = await page.$$('nav ol li button')
    if (buttons[beat.n - 1]) {
      await buttons[beat.n - 1].click()
    }
    // Beats 2/3 (map) need extra time for MapLibre tiles/layers to settle.
    const waitMs = beat.n === 2 || beat.n === 3 ? 3500 : 1800
    await new Promise((r) => setTimeout(r, waitMs))
    const path = `${OUT_DIR}/${beat.slug}.png`
    await page.screenshot({ path, fullPage: false })
    console.log(`captured ${path}`)
  }

  await browser.close()
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
