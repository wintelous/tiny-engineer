// Board variant the firmware was built for. scripts/embed_ui.py passes the
// PlatformIO option `custom_ui_board`; empty for the stock ESP32-C3-Zero builds.
export const BOARD: string = import.meta.env.VITE_TE_BOARD ?? "";

// ESP32-C3 SuperMini build: discrete RGB LED on GP6/GP7/GP10 (docs/hardware/supermini.md).
export const IS_SUPERMINI = BOARD === "supermini";
