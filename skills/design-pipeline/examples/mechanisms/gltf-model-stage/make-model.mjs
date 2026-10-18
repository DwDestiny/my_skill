// 生成 model.glb：手写最小 glTF 2.0 二进制写入器，不依赖 three。
// 用法：node make-model.mjs   输出：model.glb（同目录，约 25 KB）
// 内容：一个环面（36x18 段），含 POSITION、NORMAL、indices（uint16）和一个灰色 PBR 材质。
import {writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
const U=36,V=18,R=1,r=.38;
const pos=[],nor=[],idx=[];
for(let i=0;i<=U;i++){const a=i/U*Math.PI*2;
 for(let j=0;j<=V;j++){const b=j/V*Math.PI*2;
  const cx=Math.cos(a),sx=Math.sin(a),cb=Math.cos(b),sb=Math.sin(b);
  pos.push((R+r*cb)*cx,r*sb,(R+r*cb)*sx);nor.push(cb*cx,sb,cb*sx);}}
for(let i=0;i<U;i++)for(let j=0;j<V;j++){const a=i*(V+1)+j,b=(i+1)*(V+1)+j;idx.push(a,b,a+1,b,b+1,a+1);}
const P=new Float32Array(pos),N=new Float32Array(nor),I=new Uint16Array(idx);
const pad=n=>(4-n%4)%4;
const bin=Buffer.concat([Buffer.from(P.buffer),Buffer.from(N.buffer),Buffer.from(I.buffer),Buffer.alloc(pad(I.byteLength))]);
const mn=[1,2,3].map((_,k)=>Math.min(...pos.filter((_,i)=>i%3===k))),mx=[0,1,2].map(k=>Math.max(...pos.filter((_,i)=>i%3===k)));
const json={asset:{version:'2.0',generator:'make-model.mjs'},scene:0,scenes:[{nodes:[0]}],nodes:[{mesh:0,name:'torus'}],
 meshes:[{primitives:[{attributes:{POSITION:0,NORMAL:1},indices:2,material:0}]}],
 materials:[{pbrMetallicRoughness:{baseColorFactor:[.62,.62,.62,1],metallicFactor:.3,roughnessFactor:.45}}],
 accessors:[{bufferView:0,componentType:5126,count:P.length/3,type:'VEC3',min:mn,max:mx},
  {bufferView:1,componentType:5126,count:N.length/3,type:'VEC3'},{bufferView:2,componentType:5123,count:I.length,type:'SCALAR'}],
 bufferViews:[{buffer:0,byteOffset:0,byteLength:P.byteLength,target:34962},{buffer:0,byteOffset:P.byteLength,byteLength:N.byteLength,target:34962},
  {buffer:0,byteOffset:P.byteLength+N.byteLength,byteLength:I.byteLength,target:34963}],
 buffers:[{byteLength:bin.length}]};
let js=Buffer.from(JSON.stringify(json));js=Buffer.concat([js,Buffer.alloc(pad(js.length),32)]);
const total=12+8+js.length+8+bin.length,h=Buffer.alloc(12);
h.writeUInt32LE(0x46546C67,0);h.writeUInt32LE(2,4);h.writeUInt32LE(total,8);
const c=(len,type)=>{const b=Buffer.alloc(8);b.writeUInt32LE(len,0);b.writeUInt32LE(type,4);return b};
const out=join(dirname(fileURLToPath(import.meta.url)),'model.glb');
writeFileSync(out,Buffer.concat([h,c(js.length,0x4E4F534A),js,c(bin.length,0x004E4942),bin]));
console.log('wrote model.glb',total,'bytes');
