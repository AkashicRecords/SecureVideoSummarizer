/**
 * Basic Jest test to demonstrate the test runner functionality
 */

describe('Basic Math Operations', () => {
  test('addition works correctly', () => {
    expect(2 + 2).toBe(4);
  });

  test('subtraction works correctly', () => {
    expect(5 - 2).toBe(3);
  });

  test('multiplication works correctly', () => {
    expect(3 * 4).toBe(12);
  });

  test('division works correctly', () => {
    expect(8 / 4).toBe(2);
  });
});

describe('String Operations', () => {
  test('string concatenation works', () => {
    expect('Hello' + ' ' + 'World').toBe('Hello World');
  });

  test('string length property works', () => {
    expect('dashboard'.length).toBe(9);
  });
}); 