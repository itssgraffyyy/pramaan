import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  expect: { timeout: 30000 },
  use: { headless: true, launchOptions: { executablePath: process.env.PRAMAAN_BROWSER || undefined } },
});
