import React, {useEffect, useState} from 'react'
import io from 'socket.io-client'
import axios from 'axios'
import CameraManagement from './CameraManagement'\nimport UserManagement from './UserManagement'

const socket = io(undefined, {autoConnect: false});

function Login({onLogin}){
  const [user,setUser]=useState('admin')
  const [pw,setPw]=useState('password')
  const submit = async ()=>{
    try{
      const res = await axios.post('/api/login',{username:user,password:pw})
      onLogin(res.data.access_token)
    }catch(e){alert('Login failed')}
  }
  const [tab,setTab]=useState('cameras');

  return (
    <div style={{padding:20}}>
      <h3>Login</h3>
      <input value={user} onChange={e=>setUser(e.target.value)} placeholder="username" />
      <input type="password" value={pw} onChange={e=>setPw(e.target.value)} placeholder="password" />
      <button onClick={submit}>Login</button>
    </div>
  )
}

export default function App(){
  const [token, setToken] = useState(null)
  const [incidents, setIncidents] = useState([])

  useEffect(()=>{
    if(token){
      socket.auth = {token}
      socket.connect()
      socket.on('incident', (data)=>{
        setIncidents(prev=>[data, ...prev])
      })
    }
    const [tab,setTab]=useState('cameras');

  return ()=>{ socket.off('incident') }
  },[token])

  if(!token) return <Login onLogin={setToken} />

  const [tab,setTab]=useState('cameras');

  return (
    <div><button onClick={()=>setTab('cameras')}>Cameras</button><button onClick={()=>setTab('users')}>Users</button></div>
      <div style={{display:'flex', gap:20}}>
      <div style={{flex:2}}>
        {tab==='cameras' && <CameraManagement token={token} />}\n            {tab==='users' && <UserManagement token={token} />}
      </div>
      <div style={{width:420}}>
        <h3>Incidents</h3>
        <div style={{overflow:'auto', maxHeight: '80vh'}}>
          {incidents.map(i=>(
            <div key={i.id} style={{borderBottom:'1px solid #ddd', padding:8}}>
              <div><b>{i.label}</b> (id:{i.track_id})</div>
              <div>{new Date(i.timestamp).toLocaleString()}</div>
              <img src={i.thumbnail} style={{width: '100%', marginTop:8}} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
