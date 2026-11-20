'use client';

import React from 'react';
import type { ModelApp, Config } from '../types/modelSelection';
import type { CustomAppConfigDTO } from '@/lib/api';
import { AWS_BEDROCK_API_APP_NAME, isBedrockApiCustomApp } from '../constants/customAppConfig';
import CustomApplicationConfigSheetContent from './CustomApplicationConfigSheetContent';
import { useCustomApplicationConfigForm } from './useCustomApplicationConfigForm';

export interface EditBedrockApplicationSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingConfig: string;
  modelApps: ModelApp[];
  configs: Config[];
  onSaved?: (savedConfig: CustomAppConfigDTO) => void | Promise<void>;
}

export default function EditBedrockApplicationSheet(props: EditBedrockApplicationSheetProps) {
  const form = useCustomApplicationConfigForm({ ...props, variant: 'bedrock' });

  React.useEffect(() => {
    if (!props.open) return;
    const appName = form.currentModelApp?.name;
    if (appName && !isBedrockApiCustomApp(appName)) {
      window.alert(
        `This configuration belongs to "${appName}", not ${AWS_BEDROCK_API_APP_NAME}.`
      );
      props.onOpenChange(false);
    }
  }, [props.open, props.onOpenChange, form.currentModelApp?.name]);

  return (
    <CustomApplicationConfigSheetContent
      form={form}
      title="Edit AWS Bedrock API Configuration"
      sheetDescription="Configure AWS Bedrock Converse or OpenAI Responses endpoints on Bedrock Runtime."
      applicationLabel="Bedrock Application*"
    />
  );
}
