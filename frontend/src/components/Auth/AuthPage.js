// frontend/src/components/Auth/AuthPage.js
import React, { useState } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

function AuthPage({ onAuthSuccess }) {
  const [view, setView] = useState('login'); // 'login' or 'register'

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-blue-400 mb-2">
            RPG Game Master
          </h1>
          <p className="text-gray-400">
            AI-Powered RPG Session Manager
          </p>
        </div>

        {view === 'login' ? (
          <LoginForm
            onLoginSuccess={onAuthSuccess}
            onSwitchToRegister={() => setView('register')}
          />
        ) : (
          <RegisterForm
            onRegisterSuccess={onAuthSuccess}
            onSwitchToLogin={() => setView('login')}
          />
        )}
      </div>
    </div>
  );
}

export default AuthPage;