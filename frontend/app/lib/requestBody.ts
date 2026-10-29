export interface PreparedRequestBody {
  body: BodyInit | undefined;
  hasJsonBody: boolean;
}

export function prepareRequestBody(body: unknown): PreparedRequestBody {
  if (body === undefined) {
    return { body: undefined, hasJsonBody: false };
  }

  if (body instanceof FormData) {
    return { body, hasJsonBody: false };
  }

  return { body: JSON.stringify(body), hasJsonBody: true };
}
