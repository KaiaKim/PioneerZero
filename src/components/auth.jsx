import React from 'react';
import { useAuth } from '../hooks/useAuth';
import '../../style/global.css';

function Auth() {
  const { user, googleLogin, googleLogout } = useAuth();

  return (
    <div className="login">
      {user ? (
        <h3>관리자: {user.name || user.email} 👋
          <button id="btn-logout" onClick={googleLogout}>
          Sign out
          </button>
        </h3>
      ) : (
        <button id="btn-login" onClick={googleLogin}>
          <img src="/images/google2.png" alt="Google" />
          Sign in with Google
        </button>
      )}
    </div>
  );
}

export default Auth;

