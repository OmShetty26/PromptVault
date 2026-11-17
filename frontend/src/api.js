
const API_BASE_URL = (
    import.meta.env.VITE_API_URL ||
    (import.meta.env.DEV ? "http://localhost:8000" : "")
).replace(/\/+$/, "");

export function apiUrl(path) {
    return `${API_BASE_URL}/${path.replace(/^\/+/, "")}`;
}

export function getApiErrorMessage(
    detail,
    fallbackMessage = "Something went wrong."
) {
    // FastAPI HTTPException responses usually contain a string.
    if (typeof detail === "string" && detail.trim()) {
        return detail;
    }

    // FastAPI/Pydantic validation responses contain an array of objects.
    if (Array.isArray(detail)) {
        const messages = detail
            .map((item) => {
                if (typeof item === "string") {
                    return item;
                }

                if (
                    !item ||
                    typeof item !== "object" ||
                    typeof item.msg !== "string"
                ) {
                    return null;
                }

                const location = Array.isArray(item.loc)
                    ? item.loc.filter((part) => part !== "body").join(".")
                    : "";

                return location
                    ? `${location}: ${item.msg}`
                    : item.msg;
            })
            .filter(Boolean);

        if (messages.length > 0) {
            return messages.join(" ");
        }
    }

    return fallbackMessage;
}
