
import { sum } from '../sum';

describe('sum', () => {
  test('adds two numbers', () => {
    expect(sum(2, 3)).toBe(5);
  });

  test.each([
    [0, 0, 0],
    [1, 2, 3],
    [-1, 1, 0],
  ])('sum(%i, %i) = %i', (a, b, expected) => {
    expect(sum(a, b)).toBe(expected);
  });
});
