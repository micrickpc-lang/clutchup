import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { endpoints } from "../api/client";
import { SettingsPage } from "../pages/SettingsPage/SettingsPage";

vi.mock("../lib/telegram", () => ({ openExternal: vi.fn() }));
test("OAuth is created only after user action and shows busy state", async () => { const deferred: { resolve?: (v:{authorization_url:string})=>void } = {}; vi.spyOn(endpoints,"oauthStart").mockReturnValue(new Promise((resolve)=>{deferred.resolve=resolve})); render(<SettingsPage connected={false} onError={vi.fn()} />); expect(endpoints.oauthStart).not.toHaveBeenCalled(); fireEvent.click(screen.getByText("Подключить FACEIT аккаунт")); expect(endpoints.oauthStart).toHaveBeenCalledTimes(1); expect(screen.getByText("Открываем FACEIT…")).toBeDisabled(); deferred.resolve?.({authorization_url:"https://accounts.faceit.com"}); await waitFor(()=>expect(screen.getByText("Подключить FACEIT аккаунт")).toBeEnabled()); });
