import { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from './reduxHooks';
import { setTestNameFilled } from '@/store';
import { checkBenchmarkRunName } from '@/lib/api';

const DEBOUNCE_MS = 400;

export const TEST_NAME_REQUIRED_ERROR = 'Test name is required.';
export const TEST_NAME_DUPLICATE_ERROR =
  'A test with this name already exists. Please choose a different name.';

export interface UseTestNameValidationResult {
  isTestNameValid: boolean;
  errorMessage: string | null;
  isChecking: boolean;
}

export function useTestNameValidation(): UseTestNameValidationResult {
  const dispatch = useAppDispatch();
  const testName = useAppSelector((state) => state.modelSelection.testName);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [isTestNameValid, setIsTestNameValid] = useState(false);

  useEffect(() => {
    const trimmed = testName.trim();

    if (!trimmed) {
      setIsChecking(false);
      setIsTestNameValid(false);
      setErrorMessage(TEST_NAME_REQUIRED_ERROR);
      dispatch(setTestNameFilled(false));
      return;
    }

    setIsChecking(true);
    setIsTestNameValid(false);
    setErrorMessage(null);
    dispatch(setTestNameFilled(false));

    let cancelled = false;
    const timer = setTimeout(() => {
      void (async () => {
        try {
          const result = await checkBenchmarkRunName(trimmed);
          if (cancelled) return;

          if (result.available) {
            setIsTestNameValid(true);
            setErrorMessage(null);
            dispatch(setTestNameFilled(true));
          } else {
            setIsTestNameValid(false);
            setErrorMessage(TEST_NAME_DUPLICATE_ERROR);
            dispatch(setTestNameFilled(false));
          }
        } catch (error) {
          if (cancelled) return;
          console.error('Test name availability check failed:', error);
          setIsTestNameValid(true);
          setErrorMessage(null);
          dispatch(setTestNameFilled(true));
        } finally {
          if (!cancelled) {
            setIsChecking(false);
          }
        }
      })();
    }, DEBOUNCE_MS);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [testName, dispatch]);

  return { isTestNameValid, errorMessage, isChecking };
}
