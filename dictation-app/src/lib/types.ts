export interface Config {
  smart_format: boolean;
  device_index: number | null;
  overlay_x: number | null;
  overlay_y: number | null;
  visible: boolean;
  silence_detection: boolean;
  silence_duration: number;
  start_at_startup: boolean;
  quiet: boolean;
  auto_copy: boolean;
  pinned: boolean;
  overlay_size: "small" | "normal" | "large";
  log_to_file: boolean;
}

export interface SidecarEvent {
  event: string;
  data?: any;
  message?: string;
  state?: string;
}

export type HistoryEntry = [string, string]; // [iso_timestamp, text]
