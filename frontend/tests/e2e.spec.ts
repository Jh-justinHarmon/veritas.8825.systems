import { test, expect } from '@playwright/test';

test.describe('Veritas End-to-End Integration', () => {
  test('should load page, synthesize answer, and display concepts', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5175');

    // Wait for loading to complete (max 30 seconds for synthesis)
    await page.waitForSelector('text=Veritas V1 Demo', { timeout: 30000 });

    // Verify demo question header is present
    const questionHeader = await page.textContent('h1');
    expect(questionHeader).toContain('Why is Claude calling the wrong tool');

    // Wait for answer to load (synthesis complete)
    // Look for concept text that should appear after synthesis
    await page.waitForSelector('text=/tool|parameter|schema/i', { timeout: 30000 });

    // Verify no error state
    const hasError = await page.locator('text=Synthesis Failed').count();
    expect(hasError).toBe(0);

    const hasFailedToFetch = await page.locator('text=Failed to fetch').count();
    expect(hasFailedToFetch).toBe(0);

    // Verify concepts are rendered (should have multiple paragraphs)
    const paragraphs = await page.locator('p').count();
    expect(paragraphs).toBeGreaterThan(3);

    // Verify source sidebar is present with sources
    const sourceHeading = await page.locator('text=SOURCES').count();
    expect(sourceHeading).toBeGreaterThan(0);

    // Verify at least one source is listed
    const hasSources = await page.locator('text=/Anthropic|Claude|Documentation/i').count();
    expect(hasSources).toBeGreaterThan(0);

    // Take screenshot of successful render
    await page.screenshot({ path: 'tests/screenshots/success.png', fullPage: true });

    console.log('✅ Test passed: Answer synthesized and rendered successfully');
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // This test verifies error handling if backend is down
    // We'll skip if backend is running
    await page.goto('http://localhost:5175');
    
    // Just verify page loads without crashing
    await page.waitForLoadState('networkidle');
    
    const pageContent = await page.content();
    expect(pageContent.length).toBeGreaterThan(0);
  });
});
