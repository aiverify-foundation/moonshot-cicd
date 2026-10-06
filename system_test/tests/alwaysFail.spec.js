const { test, expect } = require('@playwright/test');

test('always fails', () => {
  expect(true).toBe(false);
});
