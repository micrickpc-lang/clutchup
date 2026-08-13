import { init, miniApp, openLink, swipeBehavior, themeParams, viewport } from "@telegram-apps/sdk";

export function initializeTelegram(): void {
  try {
    init();
    if (miniApp.mount.isAvailable()) miniApp.mount();
    if (themeParams.mount.isAvailable()) themeParams.mount();
    if (viewport.mount.isAvailable()) void viewport.mount().then(() => viewport.expand());
    if (swipeBehavior.mount.isAvailable()) { swipeBehavior.mount(); swipeBehavior.disableVertical(); }
  } catch { /* Browser preview is supported for UI development. */ }
}

export function openExternal(url: string): void {
  try { openLink(url); } catch { window.open(url, "_blank", "noopener,noreferrer"); }
}

export function telegramChat(username: string): void {
  openExternal(`https://t.me/${encodeURIComponent(username.replace(/^@/, ""))}`);
}
