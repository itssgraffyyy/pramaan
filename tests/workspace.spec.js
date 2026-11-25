import { test, expect } from '@playwright/test';

test('creates a persistent case and verifies an uploaded synthetic CSV', async ({ page }) => {
  await page.goto('http://127.0.0.1:5173/');
  await page.getByRole('button', { name: 'Case workspace' }).click();
  const name = `Synthetic browser ${Date.now()}`;
  await page.getByLabel('New case name').fill(name);
  await page.getByRole('button', { name: 'Create case' }).click();
  await expect(page.getByLabel('Select case')).toHaveText(/Synthetic browser/);
  await page.getByLabel('CSV or XLSX file').setInputFiles({ name: 'synthetic.csv', mimeType: 'text/csv', buffer: Buffer.from('caller,callee,timestamp,duration\nSYNTH-A,SYNTH-B,2026-01-01T00:00:00Z,5\n') });
  await page.getByLabel('I confirm this file contains only synthetic data.').check();
  await page.getByRole('button', { name: 'Upload and suggest mapping' }).click();
  await expect(page.getByRole('heading', { name: /Column mapping/ })).toBeVisible();
  await page.getByRole('button', { name: 'Confirm mapping & import' }).click();
  await page.getByRole('button', { name: 'Verify integrity' }).click();
  await expect(page.getByRole('status')).toContainText('Reconciliation passed');
  await page.getByRole('button', { name: /Row 2/ }).click();
  await expect(page.getByRole('dialog').getByText('SYNTH-A')).toBeVisible();
  await page.getByRole('button', { name: 'Close source record' }).click();
  await page.reload();
  await page.getByRole('button', { name: 'Case workspace' }).click();
  await page.getByLabel('Select case').selectOption({ label: name });
  await expect(page.getByText('synthetic.csv')).toBeVisible();
  await page.getByRole('button', { name: 'Open file' }).click();
  await expect(page.getByRole('heading', { name: 'Integrity & source records' })).toBeVisible();
});
