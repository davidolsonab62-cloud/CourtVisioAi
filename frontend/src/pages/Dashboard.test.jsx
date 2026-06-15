import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "./Dashboard";
import { useAuth } from "../contexts/AuthContext";

jest.mock("../contexts/AuthContext", () => ({
  useAuth: jest.fn(),
}));

jest.mock("../lib/api", () => ({ get: jest.fn(() => Promise.resolve({ data: [] })) }));

beforeEach(() => {
  jest.clearAllMocks();
});

describe("Dashboard page user actions", () => {
  test("shows upgrade button for non-premium users", async () => {
    useAuth.mockReturnValue({ user: { is_premium: false } });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const upgradeBtn = await screen.findByTestId("dashboard-upgrade-btn");
    expect(upgradeBtn).toBeInTheDocument();
    expect(upgradeBtn).toHaveAttribute("href", "/pricing");
  });
});
