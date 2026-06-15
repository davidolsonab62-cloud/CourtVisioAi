import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Admin from "./Admin";
import api from "../lib/api";

jest.mock("../lib/api", () => ({
  get: jest.fn(),
  patch: jest.fn(),
  delete: jest.fn(),
  post: jest.fn(),
}));

const mockDashboard = {
  total_users: 2,
  premium_users: 1,
  total_games: 10,
  total_predictions: 20,
  accuracy: 72.4,
  revenue_total: 1234,
};
const mockUsers = [
  { id: "user1", email: "user@courtvisionai.com", name: "Free User", role: "user", premium_until: null },
];
const mockRevenue = [];
const mockKeys = { api_sports: { host: "v1.basketball.api-sports.io", configured: false }, stripe: { configured: false } };
const mockMl = { trained: false, meta: {} };

beforeEach(() => {
  jest.clearAllMocks();
  api.get.mockImplementation((url) => {
    if (url === "/admin/dashboard") return Promise.resolve({ data: mockDashboard });
    if (url === "/admin/users") return Promise.resolve({ data: mockUsers });
    if (url === "/admin/revenue") return Promise.resolve({ data: mockRevenue });
    if (url === "/admin/api-keys") return Promise.resolve({ data: mockKeys });
    if (url === "/admin/ml/meta") return Promise.resolve({ data: mockMl });
    if (url === "/admin/api-sports/test") return Promise.resolve({ data: { status: "ok", response: { ping: true } } });
    return Promise.resolve({ data: {} });
  });
  api.patch.mockResolvedValue({ data: {} });
  api.delete.mockResolvedValue({ data: {} });
  api.post.mockResolvedValue({ data: { meta: { xgb_test_accuracy: 0.82, lgb_test_accuracy: 0.79, total_samples: 1024 } } });
  window.confirm = jest.fn(() => true);
  window.alert = jest.fn();
});

describe("Admin page button interactions", () => {
  test("renders admin buttons and triggers actions", async () => {
    render(
      <MemoryRouter>
        <Admin />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByTestId("admin-page")).toBeInTheDocument());

    const retrainBtn = screen.getByTestId("ml-retrain-btn");
    const apiSportsBtn = screen.getByTestId("api-sports-test-btn");
    const grantBtn = screen.getByTestId("grant-premium-user1");
    const suspendBtn = screen.getByTestId("suspend-user1");
    const deleteBtn = screen.getByTestId("delete-user-user1");

    fireEvent.click(apiSportsBtn);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/admin/api-sports/test"));

    fireEvent.click(retrainBtn);
    await waitFor(() => expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining("Retrain XGBoost + LightGBM ensemble")));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/admin/ml/retrain"));

    fireEvent.click(grantBtn);
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith("/admin/users/user1/role", { role: "premium" }));

    fireEvent.click(suspendBtn);
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith("/admin/users/user1/role", { role: "suspended" }));

    fireEvent.click(deleteBtn);
    await waitFor(() => expect(window.confirm).toHaveBeenCalledWith("Delete this user?"));
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith("/admin/users/user1"));
  });
});
