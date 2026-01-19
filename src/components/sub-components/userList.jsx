import React from 'react';

function UserList({ users }) {
  return (
    <div className="user-list">
      <label className="user-label">접속자 목록 ↓</label>
      <ul className="user-items">
        {users.map((userItem) => (
          <li key={userItem.id}>{userItem.name || userItem.email || 'Guest'}</li>
        ))}
      </ul>
    </div>
  );
}

export default UserList;