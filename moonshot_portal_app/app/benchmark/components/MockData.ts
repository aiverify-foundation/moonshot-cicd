export interface Provider {
  id: string;
  name: string;
  type: string;
  defaultModel: string;
  modelTextboxExplanation: string;
  configPairs: Array<{ key: string; value: string }>;
  modelToken: string;
}

export interface ModelConfig {
  id: string;
  name: string;
  modelname: string;
  provider: string;
}

export interface Config {
  id: string;
  name: string;
  connector: string;
}

export interface ModelApp{
  id: string;
  name: string;
  type: string;
  configPairs: Array<{ key: string; value: string }>;
}

export const providers: Provider[] = [
  { 
    id: "openai", 
    name: "OpenAI", 
    type: "provider", 
    defaultModel: "gpt-4", 
    modelTextboxExplanation: "Example model gpt-4 \n Refer to this link for details",
    configPairs: [
      { key: "api_key", value: "sk-" },
      { key: "base_url", value: "https://api.openai.com/v1" },
      { key: "timeout", value: "30" }
    ],
    modelToken: "model"
  },
  { 
    id: "anthropic", 
    name: "Anthropic", 
    type: "provider", 
    defaultModel: "claude-3-sonnet", 
    modelTextboxExplanation: "Example model claude-3-sonnet \n Refer to this link for details",
    configPairs: [
      { key: "api_key", value: "sk-ant-" },
      { key: "base_url", value: "https://api.anthropic.com" },
      { key: "timeout", value: "30" }
    ],
    modelToken: "model"
  },
  { 
    id: "google", 
    name: "Google", 
    type: "provider", 
    defaultModel: "gemini-pro", 
    modelTextboxExplanation: "Example model gemini-pro \n Refer to this link for details",
    configPairs: [
      { key: "api_key", value: "AIza" },
      { key: "base_url", value: "https://generativelanguage.googleapis.com/v1beta" },
      { key: "timeout", value: "30" }
    ],
    modelToken: "model"
  },
  { 
    id: "meta", 
    name: "Meta", 
    type: "provider", 
    defaultModel: "llama-2-70b", 
    modelTextboxExplanation: "Example model llama-2-70b \n Refer to this link for details",
    configPairs: [
      { key: "api_key", value: "hf_" },
      { key: "base_url", value: "https://api-inference.huggingface.co" },
      { key: "timeout", value: "60" }
    ],
    modelToken: "model"
  },
  { 
    id: "cohere", 
    name: "Cohere", 
    type: "provider", 
    defaultModel: "command", 
    modelTextboxExplanation: "Example model command \n Refer to this link for details",
    configPairs: [
      { key: "api_key", value: "cohere_" },
      { key: "base_url", value: "https://api.cohere.ai/v1" },
      { key: "timeout", value: "30" }
    ],
    modelToken: "model"
  },
  { 
    id: "mistral", 
    name: "Mistral", 
    type: "provider", 
    defaultModel: "mixtral-8x7b", 
    modelTextboxExplanation: "Example model mixtral-8x7b \n Refer to this link for details",
    configPairs: [
      { key: "api_key", value: "mistral_" },
      { key: "base_url", value: "https://api.mistral.ai/v1" },
      { key: "timeout", value: "30" }
    ],
    modelToken: "model"
  },
];

export const models: ModelConfig[] = [
  { id: "openai-gpt-4", name: "GPT-4", modelname: "gpt-4", provider: "openai" },
  { id: "openai-gpt-3.5-turbo", name: "GPT-3.5 Turbo", modelname: "gpt-3.5-turbo", provider: "openai" },
  { id: "anthropic-claude-3-opus", name: "Claude 3 Opus", modelname: "claude-3-opus", provider: "anthropic" },
  { id: "anthropic-claude-3-sonnet", name: "Claude 3 Sonnet", modelname: "claude-3-sonnet", provider: "anthropic" },
  { id: "anthropic-claude-3-haiku", name: "Claude 3 Haiku", modelname: "claude-3-haiku", provider: "anthropic" },
  { id: "google-gemini-pro", name: "Gemini Pro", modelname: "gemini-pro", provider: "google" },
  { id: "google-gemini-ultra", name: "Gemini Ultra", modelname: "gemini-ultra", provider: "google" },
  { id: "meta-llama-2-70b", name: "Llama 2 70B", modelname: "llama-2-70b", provider: "meta" },
  { id: "meta-llama-2-13b", name: "Llama 2 13B", modelname: "llama-2-13b", provider: "meta" },
  { id: "cohere-command", name: "Command", modelname: "command", provider: "cohere" },
  { id: "cohere-command-light", name: "Command Light", modelname: "command-light", provider: "cohere" },
  { id: "mistral-mistral-7b", name: "Mistral 7B", modelname: "mistral-7b", provider: "mistral" },
  { id: "mistral-mixtral-8x7b", name: "Mixtral 8x7B", modelname: "mixtral-8x7b", provider: "mistral" },
];

export const configs: Config[] = [
  { id: "neuralforge-basic", name: "Basic Configuration", connector: "neuralforge-ai" },
  { id: "neuralforge-advanced", name: "Advanced Configuration", connector: "neuralforge-ai" },
  { id: "neuralforge-premium", name: "Premium Configuration", connector: "neuralforge-ai" },
  { id: "quantummind-standard", name: "Standard Config", connector: "quantummind-studio" },
  { id: "quantummind-pro", name: "Pro Config", connector: "quantummind-studio" },
  { id: "quantummind-enterprise", name: "Enterprise Config", connector: "quantummind-studio" },
  { id: "cognitivelab-research", name: "Research Config", connector: "cognitivelab-pro" },
  { id: "cognitivelab-production", name: "Production Config", connector: "cognitivelab-pro" },
  { id: "deepthink-alpha", name: "Alpha Configuration", connector: "deepthink-platform" },
  { id: "deepthink-beta", name: "Beta Configuration", connector: "deepthink-platform" },
  { id: "deepthink-stable", name: "Stable Configuration", connector: "deepthink-platform" },
  { id: "intellisage-starter", name: "Starter Config", connector: "intellisage-hub" },
  { id: "intellisage-professional", name: "Professional Config", connector: "intellisage-hub" },
  { id: "smartbrain-core", name: "Core Configuration", connector: "smartbrain-ai" },
  { id: "smartbrain-enhanced", name: "Enhanced Configuration", connector: "smartbrain-ai" },
  { id: "neuralnet-basic", name: "Basic Setup", connector: "neuralnet-works" },
  { id: "neuralnet-optimized", name: "Optimized Setup", connector: "neuralnet-works" },
  { id: "ai-catalyst-fast", name: "Fast Configuration", connector: "ai-catalyst" },
  { id: "ai-catalyst-balanced", name: "Balanced Configuration", connector: "ai-catalyst" },
  { id: "mindforge-creative", name: "Creative Config", connector: "mindforge-studio" },
  { id: "mindforge-analytical", name: "Analytical Config", connector: "mindforge-studio" },
  { id: "cognitivemax-standard", name: "Standard Setup", connector: "cognitivemax-ai" },
  { id: "cognitivemax-premium", name: "Premium Setup", connector: "cognitivemax-ai" },
  { id: "neuralwave-basic", name: "Basic Wave Config", connector: "neuralwave-platform" },
  { id: "neuralwave-advanced", name: "Advanced Wave Config", connector: "neuralwave-platform" },
  { id: "intelligenesis-dev", name: "Development Config", connector: "intelligenesis-hub" },
  { id: "intelligenesis-prod", name: "Production Config", connector: "intelligenesis-hub" },
  { id: "deepmind-experimental", name: "Experimental Config", connector: "deepmind-lab" },
  { id: "deepmind-stable", name: "Stable Config", connector: "deepmind-lab" },
  { id: "ai-nucleus-minimal", name: "Minimal Configuration", connector: "ai-nucleus" },
  { id: "ai-nucleus-full", name: "Full Configuration", connector: "ai-nucleus" },
  { id: "neuralcore-basic", name: "Basic Core Config", connector: "neuralcore-studio" },
  { id: "neuralcore-advanced", name: "Advanced Core Config", connector: "neuralcore-studio" },
];

export const custom_connectors: ModelApp[] = [
  { id: "neuralforge-ai", name: "NeuralForge AI", type: "custom", configPairs: [{ key: "api_key", value: "nf_" }, { key: "base_url", value: "https://api.neuralforge.ai" }] },
  { id: "quantummind-studio", name: "QuantumMind Studio", type: "custom", configPairs: [{ key: "api_key", value: "qm_" }, { key: "base_url", value: "https://api.quantummind.studio" }] },
  { id: "cognitivelab-pro", name: "CognitiveLab Pro", type: "custom", configPairs: [{ key: "api_key", value: "cl_" }, { key: "base_url", value: "https://api.cognitivelab.pro" }] },
  { id: "deepthink-platform", name: "DeepThink Platform", type: "custom", configPairs: [{ key: "api_key", value: "dt_" }, { key: "base_url", value: "https://api.deepthink.platform" }] },
  { id: "intellisage-hub", name: "IntelliSage Hub", type: "custom", configPairs: [{ key: "api_key", value: "is_" }, { key: "base_url", value: "https://api.intellisage.hub" }] },
  { id: "smartbrain-ai", name: "SmartBrain AI", type: "custom", configPairs: [{ key: "api_key", value: "sb_" }, { key: "base_url", value: "https://api.smartbrain.ai" }] },
  { id: "neuralnet-works", name: "NeuralNet Works", type: "custom", configPairs: [{ key: "api_key", value: "nn_" }, { key: "base_url", value: "https://api.neuralnet.works" }] },
  { id: "ai-catalyst", name: "AI Catalyst", type: "custom", configPairs: [{ key: "api_key", value: "ac_" }, { key: "base_url", value: "https://api.ai-catalyst.com" }] },
  { id: "mindforge-studio", name: "MindForge Studio", type: "custom", configPairs: [{ key: "api_key", value: "mf_" }, { key: "base_url", value: "https://api.mindforge.studio" }] },
  { id: "cognitivemax-ai", name: "CognitiveMax AI", type: "custom", configPairs: [{ key: "api_key", value: "cm_" }, { key: "base_url", value: "https://api.cognitivemax.ai" }] },
  { id: "neuralwave-platform", name: "NeuralWave Platform", type: "custom", configPairs: [{ key: "api_key", value: "nw_" }, { key: "base_url", value: "https://api.neuralwave.platform" }] },
  { id: "intelligenesis-hub", name: "IntelliGenesis Hub", type: "custom", configPairs: [{ key: "api_key", value: "ig_" }, { key: "base_url", value: "https://api.intelligenesis.hub" }] },
  { id: "deepmind-lab", name: "DeepMind Lab", type: "custom", configPairs: [{ key: "api_key", value: "dm_" }, { key: "base_url", value: "https://api.deepmind.lab" }] },
  { id: "ai-nucleus", name: "AI Nucleus", type: "custom", configPairs: [{ key: "api_key", value: "an_" }, { key: "base_url", value: "https://api.ai-nucleus.com" }] },
  { id: "neuralcore-studio", name: "NeuralCore Studio", type: "custom", configPairs: [{ key: "api_key", value: "nc_" }, { key: "base_url", value: "https://api.neuralcore.studio" }] },
];
