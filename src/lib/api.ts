const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5225";

type ErrorResponse = {
  message?: string;
};

type ApiResponse<T> = T | ErrorResponse;

export async function postJson<TRequest, TResponse>(
  path: string,
  body: TRequest
): Promise<TResponse> {
  const url = ${API_BASE_URL};

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  let data: ApiResponse<TResponse> | null = null;

  try {
    data = (await res.json()) as ApiResponse<TResponse>;
  } catch {
    data = null;
  }

  if (!res.ok || !data) {
    const errorMessage = data?.message ?? Request failed with status .;
    throw new Error(errorMessage);
  }

  return data as TResponse;
}
