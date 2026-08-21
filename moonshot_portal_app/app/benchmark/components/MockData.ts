/**
 * Static fixtures for the **custom-application** branch of model selection only
 * (`custom_connectors`, `configs`). Standard LLM providers and models are loaded from the backend
 * (`GET /api/providers`, `GET /api/providers/by-system-name/.../latest-details`) in ModelSelectionPage.
 */

import type { Config, ModelApp } from "../types/modelSelection";

export type { Config, ModelApp };

export const configs: Config[] = [
  { id: "neuralforge-basic", name: "Basic Configuration", connector: "neuralforge-ai", configPairs: [{ key: "api_key", value: "nf_" }, { key: "base_url", value: "https://api.neuralforge.ai" }] },
  { id: "neuralforge-advanced", name: "Advanced Configuration", connector: "neuralforge-ai", configPairs: [{ key: "api_key", value: "nf_" }, { key: "base_url", value: "https://api.neuralforge.ai" }, { key: "timeout", value: "60" }] },
  { id: "neuralforge-premium", name: "Premium Configuration", connector: "neuralforge-ai", configPairs: [{ key: "api_key", value: "nf_" }, { key: "base_url", value: "https://api.neuralforge.ai" }, { key: "timeout", value: "120" }, { key: "retries", value: "3" }] },
  { id: "quantummind-standard", name: "Standard Config", connector: "quantummind-studio", configPairs: [{ key: "api_key", value: "qm_" }, { key: "base_url", value: "https://api.quantummind.studio" }] },
  { id: "quantummind-pro", name: "Pro Config", connector: "quantummind-studio", configPairs: [{ key: "api_key", value: "qm_" }, { key: "base_url", value: "https://api.quantummind.studio" }, { key: "timeout", value: "60" }] },
  { id: "quantummind-enterprise", name: "Enterprise Config", connector: "quantummind-studio", configPairs: [{ key: "api_key", value: "qm_" }, { key: "base_url", value: "https://api.quantummind.studio" }, { key: "timeout", value: "120" }, { key: "retries", value: "3" }] },
  { id: "cognitivelab-research", name: "Research Config", connector: "cognitivelab-pro", configPairs: [{ key: "api_key", value: "cl_" }, { key: "base_url", value: "https://api.cognitivelab.pro" }] },
  { id: "cognitivelab-production", name: "Production Config", connector: "cognitivelab-pro", configPairs: [{ key: "api_key", value: "cl_" }, { key: "base_url", value: "https://api.cognitivelab.pro" }, { key: "timeout", value: "60" }] },
  { id: "deepthink-alpha", name: "Alpha Configuration", connector: "deepthink-platform", configPairs: [{ key: "api_key", value: "dt_" }, { key: "base_url", value: "https://api.deepthink.platform" }] },
  { id: "deepthink-beta", name: "Beta Configuration", connector: "deepthink-platform", configPairs: [{ key: "api_key", value: "dt_" }, { key: "base_url", value: "https://api.deepthink.platform" }, { key: "timeout", value: "60" }] },
  { id: "deepthink-stable", name: "Stable Configuration", connector: "deepthink-platform", configPairs: [{ key: "api_key", value: "dt_" }, { key: "base_url", value: "https://api.deepthink.platform" }, { key: "timeout", value: "120" }, { key: "retries", value: "3" }] },
  { id: "intellisage-starter", name: "Starter Config", connector: "intellisage-hub", configPairs: [{ key: "api_key", value: "is_" }, { key: "base_url", value: "https://api.intellisage.hub" }] },
  { id: "intellisage-professional", name: "Professional Config", connector: "intellisage-hub", configPairs: [{ key: "api_key", value: "is_" }, { key: "base_url", value: "https://api.intellisage.hub" }, { key: "timeout", value: "60" }] },
  { id: "smartbrain-core", name: "Core Configuration", connector: "smartbrain-ai", configPairs: [{ key: "api_key", value: "sb_" }, { key: "base_url", value: "https://api.smartbrain.ai" }] },
  { id: "smartbrain-enhanced", name: "Enhanced Configuration", connector: "smartbrain-ai", configPairs: [{ key: "api_key", value: "sb_" }, { key: "base_url", value: "https://api.smartbrain.ai" }, { key: "timeout", value: "60" }] },
  { id: "neuralnet-basic", name: "Basic Setup", connector: "neuralnet-works", configPairs: [{ key: "api_key", value: "nn_" }, { key: "base_url", value: "https://api.neuralnet.works" }] },
  { id: "neuralnet-optimized", name: "Optimized Setup", connector: "neuralnet-works", configPairs: [{ key: "api_key", value: "nn_" }, { key: "base_url", value: "https://api.neuralnet.works" }, { key: "timeout", value: "60" }] },
  { id: "ai-catalyst-fast", name: "Fast Configuration", connector: "ai-catalyst", configPairs: [{ key: "api_key", value: "ac_" }, { key: "base_url", value: "https://api.ai-catalyst.com" }] },
  { id: "ai-catalyst-balanced", name: "Balanced Configuration", connector: "ai-catalyst", configPairs: [{ key: "api_key", value: "ac_" }, { key: "base_url", value: "https://api.ai-catalyst.com" }, { key: "timeout", value: "60" }] },
  { id: "mindforge-creative", name: "Creative Config", connector: "mindforge-studio", configPairs: [{ key: "api_key", value: "mf_" }, { key: "base_url", value: "https://api.mindforge.studio" }] },
  { id: "mindforge-analytical", name: "Analytical Config", connector: "mindforge-studio", configPairs: [{ key: "api_key", value: "mf_" }, { key: "base_url", value: "https://api.mindforge.studio" }, { key: "timeout", value: "60" }] },
  { id: "cognitivemax-standard", name: "Standard Setup", connector: "cognitivemax-ai", configPairs: [{ key: "api_key", value: "cm_" }, { key: "base_url", value: "https://api.cognitivemax.ai" }] },
  { id: "cognitivemax-premium", name: "Premium Setup", connector: "cognitivemax-ai", configPairs: [{ key: "api_key", value: "cm_" }, { key: "base_url", value: "https://api.cognitivemax.ai" }, { key: "timeout", value: "60" }] },
  { id: "neuralwave-basic", name: "Basic Wave Config", connector: "neuralwave-platform", configPairs: [{ key: "api_key", value: "nw_" }, { key: "base_url", value: "https://api.neuralwave.platform" }] },
  { id: "neuralwave-advanced", name: "Advanced Wave Config", connector: "neuralwave-platform", configPairs: [{ key: "api_key", value: "nw_" }, { key: "base_url", value: "https://api.neuralwave.platform" }, { key: "timeout", value: "60" }] },
  { id: "intelligenesis-dev", name: "Development Config", connector: "intelligenesis-hub", configPairs: [{ key: "api_key", value: "ig_" }, { key: "base_url", value: "https://api.intelligenesis.hub" }] },
  { id: "intelligenesis-prod", name: "Production Config", connector: "intelligenesis-hub", configPairs: [{ key: "api_key", value: "ig_" }, { key: "base_url", value: "https://api.intelligenesis.hub" }, { key: "timeout", value: "60" }] },
  { id: "deepmind-experimental", name: "Experimental Config", connector: "deepmind-lab", configPairs: [{ key: "api_key", value: "dm_" }, { key: "base_url", value: "https://api.deepmind.lab" }] },
  { id: "deepmind-stable", name: "Stable Config", connector: "deepmind-lab", configPairs: [{ key: "api_key", value: "dm_" }, { key: "base_url", value: "https://api.deepmind.lab" }, { key: "timeout", value: "60" }] },
  { id: "ai-nucleus-minimal", name: "Minimal Configuration", connector: "ai-nucleus", configPairs: [{ key: "api_key", value: "an_" }, { key: "base_url", value: "https://api.ai-nucleus.com" }] },
  { id: "ai-nucleus-full", name: "Full Configuration", connector: "ai-nucleus", configPairs: [{ key: "api_key", value: "an_" }, { key: "base_url", value: "https://api.ai-nucleus.com" }, { key: "timeout", value: "60" }] },
  { id: "neuralcore-basic", name: "Basic Core Config", connector: "neuralcore-studio", configPairs: [{ key: "api_key", value: "nc_" }, { key: "base_url", value: "https://api.neuralcore.studio" }] },
  { id: "neuralcore-advanced", name: "Advanced Core Config", connector: "neuralcore-studio", configPairs: [{ key: "api_key", value: "nc_" }, { key: "base_url", value: "https://api.neuralcore.studio" }, { key: "timeout", value: "60" }] },
];

export const custom_connectors: ModelApp[] = [
  { id: "neuralforge-ai", name: "NeuralForge AI", type: "custom" },
  { id: "quantummind-studio", name: "QuantumMind Studio", type: "custom" },
  { id: "cognitivelab-pro", name: "CognitiveLab Pro", type: "custom" },
  { id: "deepthink-platform", name: "DeepThink Platform", type: "custom" },
  { id: "intellisage-hub", name: "IntelliSage Hub", type: "custom" },
  { id: "smartbrain-ai", name: "SmartBrain AI", type: "custom" },
  { id: "neuralnet-works", name: "NeuralNet Works", type: "custom" },
  { id: "ai-catalyst", name: "AI Catalyst", type: "custom" },
  { id: "mindforge-studio", name: "MindForge Studio", type: "custom" },
  { id: "cognitivemax-ai", name: "CognitiveMax AI", type: "custom" },
  { id: "neuralwave-platform", name: "NeuralWave Platform", type: "custom" },
  { id: "intelligenesis-hub", name: "IntelliGenesis Hub", type: "custom" },
  { id: "deepmind-lab", name: "DeepMind Lab", type: "custom" },
  { id: "ai-nucleus", name: "AI Nucleus", type: "custom" },
  { id: "neuralcore-studio", name: "NeuralCore Studio", type: "custom" },
];
