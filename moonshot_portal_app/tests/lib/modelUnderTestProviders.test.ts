import {
  AWS_BEDROCK_ADAPTER_SYSTEM_NAME,
  isSelectableModelUnderTestProvider,
} from '@/lib/modelUnderTestProviders';

describe('isSelectableModelUnderTestProvider', () => {
  it('excludes aws_bedrock_adapter', () => {
    expect(isSelectableModelUnderTestProvider(AWS_BEDROCK_ADAPTER_SYSTEM_NAME)).toBe(
      false
    );
  });

  it('includes other providers', () => {
    expect(isSelectableModelUnderTestProvider('openai_adapter')).toBe(true);
    expect(isSelectableModelUnderTestProvider('together_adapter')).toBe(true);
  });

  it('includes missing or blank system_name', () => {
    expect(isSelectableModelUnderTestProvider(undefined)).toBe(true);
    expect(isSelectableModelUnderTestProvider('')).toBe(true);
    expect(isSelectableModelUnderTestProvider('   ')).toBe(true);
  });
});
