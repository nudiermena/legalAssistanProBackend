# Frontend Integration Guide

This guide explains how to integrate your existing frontend with the backend Supabase authentication system.

## What You Need in Your Frontend Project

### 1. Install Dependencies

Add these to your existing frontend project:

```bash
npm install @supabase/supabase-js axios
```

### 2. Environment Variables

Create a `.env` file in your frontend project:

```env
# Supabase Configuration
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# API Configuration
VITE_API_URL=http://localhost:8000
```

### 3. Supabase Client Setup

Create `src/lib/supabase.ts`:

```typescript
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Missing Supabase environment variables");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Types for user data
export interface User {
  id: string;
  email: string;
  username?: string;
  full_name?: string;
  organization?: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  last_login?: string;
  avatar_url?: string;
}
```

### 4. Authentication Context

Create `src/contexts/AuthContext.tsx`:

```typescript
import React, { createContext, useContext, useEffect, useState } from "react";
import { User, Session } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signUp: (
    email: string,
    password: string,
    userData?: any
  ) => Promise<{ error: any }>;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: any }>;
  updateProfile: (updates: any) => Promise<{ error: any }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signUp = async (email: string, password: string, userData?: any) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: userData,
      },
    });
    return { error };
  };

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { error };
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  const resetPassword = async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    return { error };
  };

  const updateProfile = async (updates: any) => {
    const { error } = await supabase.auth.updateUser({
      data: updates,
    });
    return { error };
  };

  const value = {
    user,
    session,
    loading,
    signUp,
    signIn,
    signOut,
    resetPassword,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
```

### 5. API Client

Create `src/lib/api.ts`:

```typescript
import axios from "axios";
import { supabase } from "./supabase";

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 10000,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, sign out user
      await supabase.auth.signOut();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// API functions
export const authAPI = {
  validateToken: () => api.post("/auth/validate"),
  getProfile: () => api.get("/auth/me"),
  updateProfile: (data: any) => api.put("/auth/profile", data),
  listUsers: (limit = 100, offset = 0) =>
    api.get(`/auth/users?limit=${limit}&offset=${offset}`),
  getUser: (userId: string) => api.get(`/auth/user/${userId}`),
};

export const legalAPI = {
  contractReview: (data: any) => api.post("/contract-review", data),
  legalResearch: (data: any) => api.post("/legal-research", data),
  legalChat: (data: any) => api.post("/legal-chat", data),
  documentDrafting: (data: any) => api.post("/document-drafting", data),
  casePrediction: (data: any) => api.post("/case-prediction", data),
};

export const securityAPI = {
  getStatus: () => api.get("/security/status"),
  getAlerts: (minutes = 60) => api.get(`/security/alerts?minutes=${minutes}`),
  getEvents: (minutes = 60) => api.get(`/security/events?minutes=${minutes}`),
  getUserActivity: (hours = 24) =>
    api.get(`/security/user-activity?hours=${hours}`),
  getIpActivity: (hours = 24) =>
    api.get(`/security/ip-activity?hours=${hours}`),
};

export default api;
```

### 6. Wrap Your App

In your main App component, wrap with AuthProvider:

```typescript
import { AuthProvider } from "./contexts/AuthContext";

function App() {
  return <AuthProvider>{/* Your existing app content */}</AuthProvider>;
}
```

### 7. Use Authentication in Components

Example login component:

```typescript
import { useAuth } from "../contexts/AuthContext";

function LoginForm() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const { error } = await signIn(email, password);
    if (error) {
      console.error("Login error:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button type="submit">Login</button>
    </form>
  );
}
```

Example API call:

```typescript
import { authAPI } from "../lib/api";

function ProfileComponent() {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await authAPI.getProfile();
        setProfile(response.data);
      } catch (error) {
        console.error("Error fetching profile:", error);
      }
    };
    fetchProfile();
  }, []);

  return (
    <div>
      {profile && (
        <div>
          <h2>Welcome, {profile.full_name}</h2>
          <p>Email: {profile.email}</p>
        </div>
      )}
    </div>
  );
}
```

## Backend Configuration

The backend is already configured with:

1. **Supabase integration** (`config/supabase.py`)
2. **Updated authentication endpoints** (`endpoints/auth.py`)
3. **JWT token validation middleware** (`middleware/security.py`)
4. **Environment configuration** (update your `.env` file)

## Environment Variables

Update your backend `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# CORS Configuration (add your frontend URL)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Testing

1. **Start the backend**: `uvicorn main:app --reload`
2. **Start your frontend** with the new configuration
3. **Test registration/login** through your frontend
4. **Test API calls** with authentication

## Key Points

- ✅ **Backend handles token validation** with Supabase
- ✅ **Frontend handles user registration/login** with Supabase
- ✅ **Automatic token management** in API calls
- ✅ **No duplicate authentication systems**
- ✅ **Secure JWT token validation**

The backend is ready to work with your existing frontend once you add the Supabase client and authentication context!
