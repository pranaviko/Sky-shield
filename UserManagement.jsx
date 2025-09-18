
import React, {useEffect, useState} from 'react'
import axios from 'axios'

export default function UserManagement({token}){
  const [users,setUsers] = useState([])
  const [username,setUsername] = useState('')
  const [password,setPassword] = useState('')
  const [role,setRole] = useState('operator')

  const fetch = ()=>{
    axios.get('/api/users',{headers:{Authorization:`Bearer ${token}`}})
      .then(r=>setUsers(r.data))
  }
  useEffect(()=>{fetch()},[])

  const createUser = ()=>{
    axios.post('/api/users',{username,password,role},{headers:{Authorization:`Bearer ${token}`}})
      .then(()=>{setUsername('');setPassword('');fetch()})
  }
  const deleteUser = (id)=>{
    if(!window.confirm('Delete user?')) return
    axios.delete(`/api/users/${id}`,{headers:{Authorization:`Bearer ${token}`}})
      .then(()=>fetch())
  }

  return (
    <div>
      <h3>User Management</h3>
      <div style={{marginBottom:12}}>
        <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="username"/>
        <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="password"/>
        <select value={role} onChange={e=>setRole(e.target.value)}>
          <option value="operator">Operator</option>
          <option value="admin">Admin</option>
        </select>
        <button onClick={createUser}>Create</button>
      </div>
      {users.map(u=>(
        <div key={u.id} style={{border:'1px solid #ddd',padding:8,marginBottom:6}}>
          <b>{u.username}</b> ({u.role})
          <button onClick={()=>deleteUser(u.id)} style={{marginLeft:10}}>Delete</button>
        </div>
      ))}
    </div>
  )
}
