import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.mjs',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  maxFailures: 0, // Collect every result; any failure still fails the required run.
  timeout: 240_000,
  expect: { timeout: 45_000 },
  reporter: [['line'], ['html', { open: 'never' }], ['json', { outputFile: 'test-results/results.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:8780',
    browserName: 'chromium',
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    launchOptions: {
      // WebGL on the ephemeral CI runner; this does not certify hardware GPU performance.
      args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
      ignoreDefaultArgs: ['--disable-back-forward-cache'],
    },
  },
  webServer: {
    command: 'python -m http.server 8780 --bind 127.0.0.1 --directory ../../_site',
    url: 'http://127.0.0.1:8780/asset.html',
    reuseExistingServer: false,
    timeout: 30_000,
  },
  projects: [
    { name: 'mobile', testMatch: ['mobile.spec.mjs', 'yong-access.spec.mjs'], use: { viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true } },
    { name: 'desktop', testMatch: ['desktop.spec.mjs', 'installed-models.spec.mjs', 'motion.spec.mjs', 'yong-access.spec.mjs'] },
  ],
});
