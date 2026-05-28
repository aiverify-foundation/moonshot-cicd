import userEvent from '@testing-library/user-event';
import { render, screen } from '@/tests/utils/test-utils';
import SampleSizeCard, { calculateSampleSize } from '@/app/benchmark/components/SampleSizeCard';
import type { Bundle } from '@/lib/api';

const mockBundles: Bundle[] = [
  {
    id: 'safety-bundle',
    name: 'Safety Bundle',
    description: 'Bundle description',
    category: 'Safety',
    tests: [
      {
        name: 'Test One',
        dataset: {
          id: 'ds-1',
          name: 'ds-1',
          description: '',
          num_of_dataset_prompts: 42,
        },
      },
    ],
    prompt_count: 42,
  },
];

describe('calculateSampleSize', () => {
  it('returns rounded-up sample size for 95% confidence, 5% margin, p=0.5', () => {
    expect(calculateSampleSize(95, 5, 0.5)).toBe(385);
  });
});

describe('SampleSizeCard', () => {
  it('defaults to All prompts, hides Test Run, and disables Calculated', async () => {
    render(<SampleSizeCard />, {
      preloadedState: {
        bundles: { data: mockBundles, loading: false, error: null },
        bundleSelection: { 'safety-bundle': true },
        testSelection: { 'safety-bundle': { 'Test One': true } },
      },
    });

    expect(screen.queryByRole('button', { name: /Test Run/i })).not.toBeInTheDocument();

    const calculatedToggle = screen.getByRole('button', {
      name: /Calculated — under development/i,
    });
    const allPromptsToggle = screen.getByRole('button', { name: /All prompts/i });

    expect(calculatedToggle).toBeDisabled();
    expect(allPromptsToggle).toHaveAttribute('data-state', 'on');
    expect(calculatedToggle).toHaveAttribute('data-state', 'off');

    await userEvent.click(calculatedToggle);
    expect(allPromptsToggle).toHaveAttribute('data-state', 'on');
  });
});
