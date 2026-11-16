const API_BASE_URL = (
    import.meta.env.VITE_API_URL ||
    (import.meta.env.DEV ? "http://localhost:8000" : "")
).replace(/\/+$/, "");

export function apiUrl(path) {
    return `${API_BASE_URL}/${path.replace(/^\/+/, "")}`;
}