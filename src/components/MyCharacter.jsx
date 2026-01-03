import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../../style/myChar.css';

function MyCharacter() {
  const navigate = useNavigate();

  return (
    <div>
      <button
        onClick={() => navigate('/')}
        className="close-button"
      >
        X
      </button>
    </div>
  );
}

export default MyCharacter;

