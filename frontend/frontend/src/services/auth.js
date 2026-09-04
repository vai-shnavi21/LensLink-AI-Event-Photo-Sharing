import API from "./api";

const SESSION_KEY = "ll_session";

// Restore session from localStorage on module load
let activeSession = (() => {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
})();

export const saveSession = ({ token, user }) => {
  activeSession = { token, user };
  try { localStorage.setItem(SESSION_KEY, JSON.stringify(activeSession)); } catch {}
  window.dispatchEvent(new Event("authchange"));
};

export const session = () => activeSession?.user || null;

export const signOut = () => {
  activeSession = null;
  try { localStorage.removeItem(SESSION_KEY); } catch {}
  window.dispatchEvent(new Event("authchange"));
};

export const authHeaders = () =>
  activeSession?.token ? { Authorization: `Bearer ${activeSession.token}` } : {};

export const authToken = () => activeSession?.token || null;

export const googleLogin = async (credential) => {
  const { data } = await API.post("/auth/google", { credential });
  saveSession(data);
  return data.user;
};
