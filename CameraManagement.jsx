import React, {useEffect, useState} from 'react'
import axios from 'axios'

function CameraForm({onSubmit, initial}) {
  const [name, setName] = useState(initial?.name||'Camera')
  const [source, setSource] = useState(initial?.source||'0')
  const [infer_interval, setInferInterval] = useState(initial?.infer_interval||0.5)
  const [conf_threshold, setConfThreshold] = useState(initial?.conf_threshold||0.45)
  const [enabled, setEnabled] = useState(initial?.enabled!==undefined? initial.enabled : true)

  const submit = ()=> {
    onSubmit({
      name, source, infer_interval, conf_threshold, enabled
    })
  }

  return (
    <div style={{border:'1px solid #eee', padding:12, marginBottom:12}}>
      <div><label>Name: <input value={name} onChange={e=>setName(e.target.value)} /></label></div>
      <div><label>Source: <input value={source} onChange={e=>setSource(e.target.value)} /></label></div>
      <div><label>Interval (s): <input value={infer_interval} onChange={e=>setInferInterval(e.target.value)} /></label></div>
      <div><label>Confidence: <input value={conf_threshold} onChange={e=>setConfThreshold(e.target.value)} /></label></div>
      <div><label>Enabled: <input type="checkbox" checked={enabled} onChange={e=>setEnabled(e.target.checked)} /></label></div>
      <button onClick={submit}>Save</button>
    </div>
  )
}

export default function CameraManagement({token}) {
  const [cameras, setCameras] = useState([])
  const [editing, setEditing] = useState(null)

  const fetch = ()=> {
    axios.get('/api/cameras', {headers: {Authorization: `Bearer ${token}`}})
      .then(r=>setCameras(r.data))
      .catch(e=>console.error(e))
  }

  useEffect(()=>{ fetch() },[])

  const createCam = (data)=> {
    axios.post('/api/cameras', data, {headers: {Authorization: `Bearer ${token}`}})
      .then(()=>fetch())
  }
  const updateCam = (id, data)=> {
    axios.put(`/api/cameras/${id}`, data, {headers: {Authorization: `Bearer ${token}`}})
      .then(()=>{ setEditing(null); fetch() })
  }
  const deleteCam = (id)=> {
    if(!window.confirm('Delete?')) return
    axios.delete(`/api/cameras/${id}`, {headers: {Authorization: `Bearer ${token}`}})
      .then(()=>fetch())
  }

  return (
    <div>
      <h3>Camera Management</h3>
      <h4>Create Camera</h4>
      <CameraForm onSubmit={createCam} />
      <h4>Existing Cameras</h4>
      {cameras.map(c=>(
        <div key={c.id} style={{border:'1px solid #ddd', padding:8, marginBottom:8}}>
          <div><b>{c.name}</b></div>
          <div>Source: {c.source}</div>
          <div>Interval: {c.infer_interval}s — Conf: {c.conf_threshold}</div>
          <div>
            <button onClick={()=>setEditing(c)}>Edit</button>
            <button onClick={()=>deleteCam(c.id)}>Delete</button>
          </div>
          <div style={{marginTop:8}}>
            <img src={`/camera/${c.id}/stream`} style={{width:'100%', maxHeight:240}} alt={c.name} />
          </div>
        </div>
      ))}
      {editing && (
        <div>
          <h4>Edit Camera</h4>
          <CameraForm initial={editing} onSubmit={(data)=>updateCam(editing.id, data)} />
          <button onClick={()=>setEditing(null)}>Cancel</button>
        </div>
      )}
    </div>
  )
}
