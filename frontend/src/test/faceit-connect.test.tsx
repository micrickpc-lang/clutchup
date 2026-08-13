import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { endpoints } from "../api/client";
import { ConnectFaceit } from "../features/faceit/ConnectFaceit";
import { profile } from "./fixtures";

vi.mock("../lib/telegram", () => ({ openExternal: vi.fn() }));

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

test("creates one OAuth session only after click and blocks double click", async () => {
  const deferred: { resolve?: (value: { authorization_url: string }) => void } = {};
  vi.spyOn(endpoints, "oauthStart").mockReturnValue(new Promise((resolve) => { deferred.resolve = resolve; }));
  render(<ConnectFaceit onConnected={vi.fn()} error={vi.fn()} />);
  const button = screen.getByRole("button", { name: /Войти через FACEIT/ });
  expect(endpoints.oauthStart).not.toHaveBeenCalled();
  fireEvent.click(button);
  fireEvent.click(button);
  expect(endpoints.oauthStart).toHaveBeenCalledTimes(1);
  expect(screen.getByText("Открываем FACEIT…")).toBeDisabled();
  deferred.resolve?.({ authorization_url: "https://accounts.faceit.com" });
  await waitFor(() => expect(screen.getByText("Проверяем подключение…")).toBeDisabled());
});

test("shows API error and allows retry", async () => {
  const error = vi.fn();
  vi.spyOn(endpoints, "oauthStart").mockRejectedValue(new Error("network"));
  render(<ConnectFaceit onConnected={vi.fn()} error={error} />);
  fireEvent.click(screen.getByRole("button", { name: /Войти через FACEIT/ }));
  await waitFor(() => expect(error).toHaveBeenCalled());
  expect(screen.getByRole("button", { name: /Войти через FACEIT/ })).toBeEnabled();
});

test("polling refreshes profile and stops after success", async () => {
  vi.useFakeTimers();
  const connected = vi.fn();
  vi.spyOn(endpoints, "oauthStart").mockResolvedValue({ authorization_url: "https://accounts.faceit.com" });
  vi.spyOn(endpoints, "profile").mockResolvedValue(profile);
  const view = render(<ConnectFaceit onConnected={connected} error={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: /Войти через FACEIT/ }));
  await act(async () => { await Promise.resolve(); });
  await act(async () => { await vi.advanceTimersByTimeAsync(2_000); });
  expect(connected).toHaveBeenCalledWith(profile);
  const calls = vi.mocked(endpoints.profile).mock.calls.length;
  await act(async () => { await vi.advanceTimersByTimeAsync(10_000); });
  expect(endpoints.profile).toHaveBeenCalledTimes(calls);
  view.unmount();
  expect(vi.getTimerCount()).toBe(0);
});
