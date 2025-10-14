export interface Provider {
  value: string;
  label: string;
  type: string;
}

export interface Model {
  value: string;
  label: string;
  provider: string;
}

export interface Config {
  value: string;
  label: string;
  connector: string;
}

export const providers: Provider[] = [
  { value: "openai", label: "OpenAI", type: "provider" },
  { value: "anthropic", label: "Anthropic", type: "provider" },
  { value: "google", label: "Google", type: "provider" },
  { value: "meta", label: "Meta", type: "provider" },
  { value: "cohere", label: "Cohere", type: "provider" },
  { value: "mistral", label: "Mistral", type: "provider" },
];

export const models: Model[] = [
  { value: "openai-gpt-4", label: "GPT-4", provider: "openai" },
  { value: "openai-gpt-3.5-turbo", label: "GPT-3.5 Turbo", provider: "openai" },
  { value: "anthropic-claude-3-opus", label: "Claude 3 Opus", provider: "anthropic" },
  { value: "anthropic-claude-3-sonnet", label: "Claude 3 Sonnet", provider: "anthropic" },
  { value: "anthropic-claude-3-haiku", label: "Claude 3 Haiku", provider: "anthropic" },
  { value: "google-gemini-pro", label: "Gemini Pro", provider: "google" },
  { value: "google-gemini-ultra", label: "Gemini Ultra", provider: "google" },
  { value: "meta-llama-2-70b", label: "Llama 2 70B", provider: "meta" },
  { value: "meta-llama-2-13b", label: "Llama 2 13B", provider: "meta" },
  { value: "cohere-command", label: "Command", provider: "cohere" },
  { value: "cohere-command-light", label: "Command Light", provider: "cohere" },
  { value: "mistral-mistral-7b", label: "Mistral 7B", provider: "mistral" },
  { value: "mistral-mixtral-8x7b", label: "Mixtral 8x7B", provider: "mistral" },
];

export const configs: Config[] = [
  { value: "neuralforge-basic", label: "Basic Configuration", connector: "neuralforge-ai" },
  { value: "neuralforge-advanced", label: "Advanced Configuration", connector: "neuralforge-ai" },
  { value: "neuralforge-premium", label: "Premium Configuration", connector: "neuralforge-ai" },
  { value: "quantummind-standard", label: "Standard Config", connector: "quantummind-studio" },
  { value: "quantummind-pro", label: "Pro Config", connector: "quantummind-studio" },
  { value: "quantummind-enterprise", label: "Enterprise Config", connector: "quantummind-studio" },
  { value: "cognitivelab-research", label: "Research Config", connector: "cognitivelab-pro" },
  { value: "cognitivelab-production", label: "Production Config", connector: "cognitivelab-pro" },
  { value: "deepthink-alpha", label: "Alpha Configuration", connector: "deepthink-platform" },
  { value: "deepthink-beta", label: "Beta Configuration", connector: "deepthink-platform" },
  { value: "deepthink-stable", label: "Stable Configuration", connector: "deepthink-platform" },
  { value: "intellisage-starter", label: "Starter Config", connector: "intellisage-hub" },
  { value: "intellisage-professional", label: "Professional Config", connector: "intellisage-hub" },
  { value: "smartbrain-core", label: "Core Configuration", connector: "smartbrain-ai" },
  { value: "smartbrain-enhanced", label: "Enhanced Configuration", connector: "smartbrain-ai" },
  { value: "neuralnet-basic", label: "Basic Setup", connector: "neuralnet-works" },
  { value: "neuralnet-optimized", label: "Optimized Setup", connector: "neuralnet-works" },
  { value: "ai-catalyst-fast", label: "Fast Configuration", connector: "ai-catalyst" },
  { value: "ai-catalyst-balanced", label: "Balanced Configuration", connector: "ai-catalyst" },
  { value: "mindforge-creative", label: "Creative Config", connector: "mindforge-studio" },
  { value: "mindforge-analytical", label: "Analytical Config", connector: "mindforge-studio" },
  { value: "cognitivemax-standard", label: "Standard Setup", connector: "cognitivemax-ai" },
  { value: "cognitivemax-premium", label: "Premium Setup", connector: "cognitivemax-ai" },
  { value: "neuralwave-basic", label: "Basic Wave Config", connector: "neuralwave-platform" },
  { value: "neuralwave-advanced", label: "Advanced Wave Config", connector: "neuralwave-platform" },
  { value: "intelligenesis-dev", label: "Development Config", connector: "intelligenesis-hub" },
  { value: "intelligenesis-prod", label: "Production Config", connector: "intelligenesis-hub" },
  { value: "deepmind-experimental", label: "Experimental Config", connector: "deepmind-lab" },
  { value: "deepmind-stable", label: "Stable Config", connector: "deepmind-lab" },
  { value: "ai-nucleus-minimal", label: "Minimal Configuration", connector: "ai-nucleus" },
  { value: "ai-nucleus-full", label: "Full Configuration", connector: "ai-nucleus" },
  { value: "neuralcore-basic", label: "Basic Core Config", connector: "neuralcore-studio" },
  { value: "neuralcore-advanced", label: "Advanced Core Config", connector: "neuralcore-studio" },
];

export const custom_connectors: Provider[] = [
  { value: "neuralforge-ai", label: "NeuralForge AI", type: "custom" },
  { value: "quantummind-studio", label: "QuantumMind Studio", type: "custom" },
  { value: "cognitivelab-pro", label: "CognitiveLab Pro", type: "custom" },
  { value: "deepthink-platform", label: "DeepThink Platform", type: "custom" },
  { value: "intellisage-hub", label: "IntelliSage Hub", type: "custom" },
  { value: "smartbrain-ai", label: "SmartBrain AI", type: "custom" },
  { value: "neuralnet-works", label: "NeuralNet Works", type: "custom" },
  { value: "ai-catalyst", label: "AI Catalyst", type: "custom" },
  { value: "mindforge-studio", label: "MindForge Studio", type: "custom" },
  { value: "cognitivemax-ai", label: "CognitiveMax AI", type: "custom" },
  { value: "neuralwave-platform", label: "NeuralWave Platform", type: "custom" },
  { value: "intelligenesis-hub", label: "IntelliGenesis Hub", type: "custom" },
  { value: "deepmind-lab", label: "DeepMind Lab", type: "custom" },
  { value: "ai-nucleus", label: "AI Nucleus", type: "custom" },
  { value: "neuralcore-studio", label: "NeuralCore Studio", type: "custom" },
];
