import { WEBUI_API_BASE_URL } from '$lib/constants';

export const getContextState = async (token: string, chatId: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${chatId}/context/state`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` }),
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

export const updateContextSettings = async (token: string, chatId: string, settings: object) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${chatId}/context/settings`, {
    method: 'PUT',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(settings),
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

export const getContextSegments = async (token: string, chatId: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${chatId}/context/segments`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` }),
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

export const getActiveSegment = async (token: string, chatId: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${chatId}/context/segments/active`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` }),
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

export const triggerCompaction = async (token: string, chatId: string, force: boolean = false) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${chatId}/context/compact`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify({ force }),
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

export const rollbackSegment = async (token: string, chatId: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${chatId}/context/rollback`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` }),
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

export const getCurrentSummary = async (token: string, chatId: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${chatId}/context/summary`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` }),
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

export const previewContext = async (token: string, chatId: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${chatId}/context/preview`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` }),
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

export const resetCompression = async (token: string, chatId: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${chatId}/context/reset`, {
    method: 'DELETE',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` }),
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

export const cleanupExpiredSegments = async (token: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/chats/context/cleanup`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` }),
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
