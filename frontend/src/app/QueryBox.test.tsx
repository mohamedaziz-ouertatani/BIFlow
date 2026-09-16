import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import QueryBox from "./QueryBox";

function mockFetchOnce(response: Partial<Response> & { jsonBody?: unknown }) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: response.ok ?? true,
    status: response.status ?? 200,
    json: async () => response.jsonBody,
  } as Response);
}

afterEach(() => {
  jest.restoreAllMocks();
});

describe("QueryBox", () => {
  it("submits the question and renders the answer", async () => {
    mockFetchOnce({ jsonBody: { answer: "Revenue is healthy." } });

    render(<QueryBox />);
    fireEvent.change(screen.getByPlaceholderText(/ask a question/i), {
      target: { value: "How is revenue?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /ask/i }));

    expect(await screen.findByText("Revenue is healthy.")).toBeInTheDocument();
    expect(screen.getByText("How is revenue?")).toBeInTheDocument();
  });

  it("disables the input and button while waiting for the answer", async () => {
    let resolveFetch: (value: unknown) => void = () => {};
    global.fetch = jest.fn().mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve;
      })
    );

    render(<QueryBox />);
    fireEvent.change(screen.getByPlaceholderText(/ask a question/i), {
      target: { value: "How is revenue?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /ask/i }));

    expect(screen.getByPlaceholderText(/ask a question/i)).toBeDisabled();
    expect(screen.getByRole("button", { name: /thinking/i })).toBeDisabled();

    resolveFetch({ ok: true, status: 200, json: async () => ({ answer: "ok" }) });
    await waitFor(() => expect(screen.getByPlaceholderText(/ask a question/i)).not.toBeDisabled());
  });

  it("shows the server's error detail when the request fails", async () => {
    mockFetchOnce({ ok: false, status: 503, jsonBody: { detail: "Local LLM unavailable — is Ollama running?" } });

    render(<QueryBox />);
    fireEvent.change(screen.getByPlaceholderText(/ask a question/i), {
      target: { value: "How is revenue?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /ask/i }));

    expect(await screen.findByText(/local llm unavailable/i)).toBeInTheDocument();
  });

  it("does not submit an empty question", () => {
    global.fetch = jest.fn();

    render(<QueryBox />);
    fireEvent.click(screen.getByRole("button", { name: /ask/i }));

    expect(global.fetch).not.toHaveBeenCalled();
  });
});
