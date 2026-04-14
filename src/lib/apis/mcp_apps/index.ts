import { WEBUI_API_BASE_URL } from '$lib/constants';

export const getMcpApps = async (token: string = '') => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/mcp_apps/`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail;
      console.error(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const createMcpApp = async (token: string, app: object) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/mcp_apps/create`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(app),
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail;
      console.error(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const getMcpAppById = async (token: string, id: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/mcp_apps/id/${id}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail;
      console.error(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const updateMcpAppById = async (token: string, id: string, app: object) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/mcp_apps/id/${id}/update`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(app),
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail;
      console.error(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const toggleMcpAppById = async (token: string, id: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/mcp_apps/id/${id}/toggle`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail;
      console.error(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const deleteMcpAppById = async (token: string, id: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/mcp_apps/id/${id}/delete`, {
    method: 'DELETE',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail;
      console.error(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const testMcpAppConnection = async (token: string, id: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/mcp_apps/id/${id}/test`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail;
      console.error(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const testMcpAppConnectionDirect = async (token: string, connectionData: object) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/mcp_apps/test`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(connectionData),
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail;
      console.error(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const callMcpAppTool = async (
  token: string,
  appId: string,
  toolName: string,
  params: Record<string, any> = {},
  confirmed: boolean = false,
): Promise<{
  content?: any;
  ui_resource?: { uri?: string; mimeType?: string; text?: string; blob?: string } | null;
  requires_confirmation?: boolean;
  tool_name?: string;
  display_name?: string;
  confirmation_widget_id?: string | null;
  params?: Record<string, any>;
}> => {
  const res = await fetch(
    `${WEBUI_API_BASE_URL}/mcp_apps/id/${appId}/tools/${encodeURIComponent(toolName)}/call`,
    {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ params, confirmed }),
    },
  );

  if (!res.ok) {
    let detail;
    try {
      detail = (await res.json())?.detail;
    } catch {
      detail = res.statusText;
    }
    throw detail;
  }

  return res.json();
};

export const updateMcpAppAccessGrants = async (token: string, id: string, accessGrants: any[]) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/mcp_apps/id/${id}/access/update`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      access_grants: accessGrants,
    }),
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail;
      console.error(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};
