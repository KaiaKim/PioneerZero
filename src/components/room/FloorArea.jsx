import React from 'react';

function FloorArea({ characters }) {
  const xyCells = ['Y1', 'Y2', 'Y3', 'Y4', 'X1', 'X2', 'X3', 'X4'];
  const abCells = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4'];

  return (
    <div className="floor-area">
      <div className="floor-grid">
        <div className="floor-section team-blue">
          <div className="grid-3d">
            {xyCells.map((cellId) => {
              const cellCharacter = characters.find(c => c.pos === cellId);
              return (
                <div key={cellId} className="cell">
                  {cellId}
                  {cellCharacter && (
                    <img
                      src={cellCharacter.token_image}
                      alt={cellCharacter.name}
                      className="token"
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
        <div className="floor-section team-white">
          <div className="grid-3d">
            {abCells.map((cellId) => {
              const cellCharacter = characters.find(c => c.pos === cellId);
              return (
                <div key={cellId} className="cell">
                  {cellId}
                  {cellCharacter && (
                    <img
                      src={cellCharacter.token_image}
                      alt={cellCharacter.name}
                      className="token"
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default FloorArea;

