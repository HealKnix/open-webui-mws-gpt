import { WEBUI_API_BASE_URL } from '$lib/constants';

export const createNewWidget = async (token: string, widget: object) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/widgets/create`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      ...widget,
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

export const getWidgets = async (token: string = '') => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/widgets/`, {
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
    .then((json) => {
      return json;
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

export const getWidgetList = async (token: string = '') => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/widgets/list`, {
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
    .then((json) => {
      return json;
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

export const getWidgetItems = async (
  token: string = '',
  query: string | null = null,
  viewOption: string | null = null,
  page: number | null = null,
) => {
  let error = null;

  const searchParams = new URLSearchParams();
  if (query) searchParams.append('query', query);
  if (viewOption) searchParams.append('view_option', viewOption);
  if (page) searchParams.append('page', page.toString());

  const res = await fetch(`${WEBUI_API_BASE_URL}/widgets/list?${searchParams.toString()}`, {
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
    .then((json) => {
      return json;
    })
    .catch((err) => {
      error = err;
      console.error(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const exportWidgets = async (token: string = '') => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/widgets/export`, {
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
    .then((json) => {
      return json;
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

export const getWidgetById = async (token: string, id: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/widgets/id/${id}`, {
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
    .then((json) => {
      return json;
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

export const updateWidgetById = async (token: string, id: string, widget: object) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/widgets/id/${id}/update`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      ...widget,
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

export const updateWidgetAccessGrants = async (token: string, id: string, accessGrants: any[]) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/widgets/id/${id}/access/update`, {
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

export const toggleWidgetById = async (token: string, id: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/widgets/id/${id}/toggle`, {
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
    .then((json) => {
      return json;
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

export const deleteWidgetById = async (token: string, id: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/widgets/id/${id}/delete`, {
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
    .then((json) => {
      return json;
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
