import { invoke } from "@tauri-apps/api/core";
import type { Config } from "./types";

export async function readConfig(): Promise<Config> {
  return await invoke("read_config");
}

export async function saveConfig(config: Config): Promise<void> {
  await invoke("save_config", { config });
}

export async function saveConfigField(
  key: string,
  value: unknown,
): Promise<void> {
  await invoke("save_config_field", { key, value });
}

export async function readApiKey(): Promise<string> {
  return await invoke("read_api_key");
}

export async function saveApiKey(key: string): Promise<void> {
  await invoke("save_api_key", { key });
}

export async function validateApiKey(key: string): Promise<boolean> {
  return await invoke("validate_api_key", { key });
}
