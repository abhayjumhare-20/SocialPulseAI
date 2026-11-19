const BASE=import.meta.env.VITE_API_URL||'http://localhost:5000/api';
export function token(){return localStorage.getItem('sp_token')}
export async function api(path,opts={}) {
 const headers={'Content-Type':'application/json',...(opts.headers||{})};
 if(token()) headers.Authorization=`Bearer ${token()}`;
 const res=await fetch(BASE+path,{...opts,headers});
 const data=opts.raw?res:await res.json().catch(()=>({}));
 if(!res.ok) throw new Error(data.error||'Request failed');
 return data;
}
