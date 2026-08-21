export const INTERPRETATION_POINTS = [
  {
    label: 'Score interpretation',
    body:
      'The test scores reflect the average performance of the LLM App/ Model under test across the selected risk categories and prompts. A score of 90 means the LLM App/ Model produces unsafe responses at a rate of 10%. To further interpret the hazard categories, sample prompts can be found in the public dataset in AI Verify Foundation\'s GitHub repo.',
  },
  {
    label: 'Limitations',
    body:
      'A perfect score indicates minimal baseline risks. However, it does not guarantee the absolute safety of the LLM App/ Model under test. Other testing methodologies, such as red teaming and custom app testing, are encouraged for higher safety requirements.',
  },
  {
    label: 'Threshold setting',
    body:
      'Businesses need to define their threshold based on the application\'s risk tolerance. AI Verify Foundation currently does not set a threshold.',
  },
] as const;

export const USE_CASE_COPY =
  'The AI Verify Safety Benchmark for Singapore evaluates general-purpose AI chat systems for safe behaviour across a comprehensive set of risk categories defined by the Infocomm Media Development Authority of Singapore (IMDA). Results are intended to inform procurement decisions, deployment risk assessment, and responsible AI governance across organisations in Singapore.';

export const REPORT_METADATA = {
  testProvider: 'AI Verify Foundation',
  testTool: 'Project Moonshot V1',
} as const;

export const SCORE_BREAKDOWN_TITLE = 'Score Breakdown by Risk Category';

export const SCORE_BREAKDOWN_SUBTEXT =
  "Each bar shows the model's score (0–100) with confidence interval whiskers at 95% level (only when margin of error can be calculated). Higher scores indicate stronger safety performance.";

export const FOOTER_LINK_URL =
  'https://github.com/aiverify-foundation/moonshot-cicd';

export const FOOTER_LINKS = ['Privacy', 'Policies', 'Terms of Service'] as const;
