import Sidebar from "./components/Sidebar";
import Editor from "./components/Editor";

import { useState, useEffect } from "react";
import { Routes, Route, useNavigate, Outlet } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./components/Login"
import Register from "./components/Register"
import LandingPage from "./components/LandingPage";
import { apiUrl } from "./api.js";

function AppLayout({ prompts, setPrompts, onLogout }) {
    return (
        <div
            className="
                flex
                h-dvh
                overflow-hidden
                bg-zinc-950
                text-zinc-100
                font-sans
                antialiased
            "
        >
            <Sidebar
                prompts={prompts}
                setPrompts={setPrompts}
                onLogout={onLogout}
            />

            <main
                className="
                    flex-1
                    min-w-0
                    h-full
                    flex
                    flex-col
                    overflow-hidden
                "
            >
                <Outlet />
            </main>
        </div>
    );
}

function ProjectApp() {
    const [savedPrompts, setSavedPrompts] = useState([]);
    const [, setCurrentUser] = useState(null);
    const [authStatus, setAuthStatus] = useState("checking");
    const navigate = useNavigate();

    useEffect(() => {
        async function checkAuth() {
            try {
                const response = await fetch(
                    apiUrl("/auth/me"),
                    { 
                        credentials: "include"
                    }
                );

                if (response.ok) {
                    const user = await response.json();

                    setCurrentUser(user);
                    setAuthStatus("authenticated");
                } else {
                    setCurrentUser(null);
                    setAuthStatus("unauthenticated");
                }
            } catch {
                setCurrentUser(null);
                setAuthStatus("unauthenticated");
            }
        }

        checkAuth();
    }, []);

    useEffect(() => {
        if (authStatus !== "authenticated") {
            return;
        }

        const fetchPrompts = async () => {
            try {
                const response = await fetch(
                    apiUrl("/api/prompts"),
                    {
                        credentials: "include"
                    }
                );

                if (!response.ok) {
                    throw new Error(`Failed to fetch prompts: ${response.status}`);
                }

                const data = await response.json();

                setSavedPrompts(data);
            } catch (error) {
                console.error("Failed to hydrate prompts:", error);
            }
        };

        fetchPrompts();
    }, [authStatus]);


    const handleLogout = async () => {
        try {
            const response = await fetch(
                apiUrl("/auth/logout"),
                {
                    method: "POST",
                    credentials: "include"
                }
            );

            if (!response.ok) {
                throw new Error("Logout failed");
            }

            setCurrentUser(null);
            setAuthStatus("unauthenticated");
            setSavedPrompts([]);

            navigate("/login");
        } catch (error) {
            console.error("Failed to log out:", error);
        }
    };

    return (
        <Routes>
            {/* Public */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login setAuthStatus={setAuthStatus} setCurrentUser={setCurrentUser}/>} />
            <Route path="/register" element={<Register setAuthStatus={setAuthStatus} setCurrentUser={setCurrentUser}/>} />

            {/* Protected */}
            <Route
                element={
                    <ProtectedRoute authStatus={authStatus}>
                        <AppLayout
                            prompts={savedPrompts}
                            setPrompts={setSavedPrompts}
                            onLogout={handleLogout}
                        />
                    </ProtectedRoute>
                }
            >
                <Route path="/home" element={<Dashboard />} />
                <Route
                    path="/create"
                    element={<Editor modifyPrompts={setSavedPrompts} />}
                />
                <Route
                    path="api/prompts/:id"
                    element={<Editor modifyPrompts={setSavedPrompts} />}
                />
            </Route>
        </Routes>
    );
}

function App() {
    return <ProjectApp />;
}

export default App;