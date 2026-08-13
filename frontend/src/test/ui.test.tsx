import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { AppLayout } from "../components/layout/AppLayout";
import { MatchesPage } from "../pages/MatchesPage/MatchesPage";
import { ProfilePage } from "../pages/ProfilePage/ProfilePage";
import { SearchPage } from "../pages/SearchPage/SearchPage";
import { StatisticsPage } from "../pages/StatisticsPage/StatisticsPage";
import { player, profile } from "./fixtures";

test("renders loading and empty search states", () => { const { rerender } = render(<SearchPage player={null} loading busy={false} error="" retry={vi.fn()} swipe={vi.fn()} details={vi.fn()} filters={vi.fn()} />); expect(document.querySelector(".skeleton")).toBeInTheDocument(); rerender(<SearchPage player={null} loading={false} busy={false} error="" retry={vi.fn()} swipe={vi.fn()} details={vi.fn()} filters={vi.fn()} />); expect(screen.getByText("SIGNAL QUIET")).toBeInTheDocument(); });
test("party button calls like", () => { const swipe=vi.fn(); render(<SearchPage player={player} loading={false} busy={false} error="" retry={vi.fn()} swipe={swipe} details={vi.fn()} filters={vi.fn()} />); fireEvent.click(screen.getByLabelText("Add to party")); expect(swipe).toHaveBeenCalledWith("like"); });
test("four item navigation works", () => { const nav=vi.fn(); render(<AppLayout tab="search" onTab={nav}><div /></AppLayout>); expect(screen.getAllByRole("button")).toHaveLength(4); fireEvent.click(screen.getByText("INBOX")); expect(nav).toHaveBeenCalledWith("statistics"); });
test("matches online filter uses real presence", () => { render(<MatchesPage items={[{...player,matched_at:new Date().toISOString()}]} loading={false} error="" retry={vi.fn()} select={vi.fn()} />); const tabs=screen.getAllByRole("tab"); fireEvent.click(tabs[2]); expect(screen.getByText("m0NESY")).toBeInTheDocument(); });
test("profile renders real faceit data", () => { render(<ProfilePage profile={profile} edit={vi.fn()} settings={vi.fn()} />); expect(screen.getByText("Me")).toBeInTheDocument(); expect(screen.getByText("2500")).toBeInTheDocument(); });
test("statistics filters render", () => { render(<StatisticsPage preferences={profile.preferences} statistics={profile.statistics} loading={false} error="" save={vi.fn()} />); expect(document.querySelector(".filter-form")).toBeInTheDocument(); expect(document.querySelector(".stats-section")).toBeInTheDocument(); });
