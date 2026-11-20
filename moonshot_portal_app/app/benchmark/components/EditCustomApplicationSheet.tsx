'use client';

import React from 'react';
import type { ModelApp, Config } from '../types/modelSelection';
import type { CustomAppConfigDTO } from '@/lib/api';
import CustomApplicationConfigSheetContent from './CustomApplicationConfigSheetContent';
import { useCustomApplicationConfigForm } from './useCustomApplicationConfigForm';

export interface EditCustomApplicationSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingConfig: string;
  modelApps: ModelApp[];
  configs: Config[];
  onSaved?: (savedConfig: CustomAppConfigDTO) => void | Promise<void>;
}

export default function EditCustomApplicationSheet(props: EditCustomApplicationSheetProps) {
  const form = useCustomApplicationConfigForm({ ...props, variant: 'custom' });

  return (
    <CustomApplicationConfigSheetContent
      form={form}
      title="Edit Custom Application Configuration"
      sheetDescription="Configure the custom application endpoints and settings."
    />
  );
}
