# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: e2e.spec.ts >> Veritas End-to-End Integration >> should load page, synthesize answer, and display concepts
- Location: tests/e2e.spec.ts:4:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.waitForSelector: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('text=/veritas|technical synthesis/i') to be visible

```

# Page snapshot

```yaml
- generic [ref=e4]:
  - generic [ref=e5]: Synthesis Failed
  - generic [ref=e6]: "Synthesis failed: Not Found"
  - button "Retry" [ref=e7] [cursor=pointer]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Veritas End-to-End Integration', () => {
  4  |   test('should load page, synthesize answer, and display concepts', async ({ page }) => {
  5  |     // Navigate to the app
  6  |     await page.goto('http://localhost:5173');
  7  | 
  8  |     // Wait for loading to complete (max 30 seconds for synthesis)
> 9  |     await page.waitForSelector('text=/veritas|technical synthesis/i', { timeout: 30000 });
     |                ^ Error: page.waitForSelector: Test timeout of 30000ms exceeded.
  10 | 
  11 |     // Verify demo question header is present
  12 |     const questionHeader = await page.textContent('h1');
  13 |     expect(questionHeader).toContain('Why is Claude calling the wrong tool');
  14 | 
  15 |     // Wait for answer to load (synthesis complete)
  16 |     // Look for concept text that should appear after synthesis
  17 |     await page.waitForSelector('text=/tool|parameter|schema/i', { timeout: 30000 });
  18 | 
  19 |     // Verify no error state
  20 |     const hasError = await page.locator('text=Synthesis Failed').count();
  21 |     expect(hasError).toBe(0);
  22 | 
  23 |     const hasFailedToFetch = await page.locator('text=Failed to fetch').count();
  24 |     expect(hasFailedToFetch).toBe(0);
  25 | 
  26 |     // Verify concepts are rendered (should have multiple paragraphs)
  27 |     const paragraphs = await page.locator('p').count();
  28 |     expect(paragraphs).toBeGreaterThan(3);
  29 | 
  30 |     // Verify source sidebar is present with sources
  31 |     const sourceHeading = await page.locator('text=SOURCES').count();
  32 |     expect(sourceHeading).toBeGreaterThan(0);
  33 | 
  34 |     // Verify at least one source is listed
  35 |     const hasSources = await page.locator('text=/Anthropic|Claude|Documentation/i').count();
  36 |     expect(hasSources).toBeGreaterThan(0);
  37 | 
  38 |     // Take screenshot of successful render
  39 |     await page.screenshot({ path: 'tests/screenshots/success.png', fullPage: true });
  40 | 
  41 |     console.log('✅ Test passed: Answer synthesized and rendered successfully');
  42 |   });
  43 | 
  44 |   test('should handle API errors gracefully', async ({ page }) => {
  45 |     // This test verifies error handling if backend is down
  46 |     // We'll skip if backend is running
  47 |     await page.goto('http://localhost:5173');
  48 |     
  49 |     // Just verify page loads without crashing
  50 |     await page.waitForLoadState('networkidle');
  51 |     
  52 |     const pageContent = await page.content();
  53 |     expect(pageContent.length).toBeGreaterThan(0);
  54 |   });
  55 | });
  56 | 
```