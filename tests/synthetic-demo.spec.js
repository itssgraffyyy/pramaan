import { test, expect } from '@playwright/test';

test('loads computed synthetic data and opens a referenced source row', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5173/');
  await page.getByRole('button', { name: /load synthetic demo/i }).first().click();
  await expect(page.getByRole('heading', { name: 'Evidence at a glance' })).toBeVisible();
  await expect(page.getByText('Original records').locator('..').locator('strong')).toHaveText('8');
  await expect(page.getByRole('heading', { name: 'Validation issues' })).toBeVisible();
  await page.getByRole('button', { name: /Row 2/ }).first().click();
  await expect(page.getByRole('dialog', { name: 'Original record' })).toBeVisible();
  await expect(page.getByRole('dialog').getByText('operator_a.csv')).toBeVisible();
  await expect(page.getByRole('dialog').getByText('SYNTH-A')).toBeVisible();
  await page.getByRole('button', { name: 'Close source record' }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(errors).toEqual([]);
});
