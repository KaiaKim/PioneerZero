import React from 'react';
import { useAuth } from '../hooks/useAuth';
import '../../style/global.css';

function Auth() {
  const { user, loginSIWG } = useAuth();

  return (
    <div className="login">
      {user ? (
        <h3>관리자: {user.name || user.email} 👋</h3>
      ) : (
        <button id="btn-siwg" onClick={loginSIWG}>
          <img src="/images/google2.png" alt="Google" />
          Sign in with Google
        </button>
      )}
    </div>
  );
}

export default Auth;

