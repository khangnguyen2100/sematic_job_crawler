import { adminApi } from '@/services/api';
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();
  
  try {
    const isAuthenticated = adminApi.isAuthenticated();

    // If not authenticated, redirect to login with the current location as state
    // so we can redirect back after successful login
    if (!isAuthenticated) {
      return <Navigate to="/admin/login" state={{ from: location }} replace />;
    }

    return children as JSX.Element;
  } catch (error) {
    // If there's an error checking authentication, redirect to login
    console.error('Error checking authentication:', error);
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }
}
