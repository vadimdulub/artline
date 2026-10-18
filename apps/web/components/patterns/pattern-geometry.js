function spPolar(radius,angle){const a=angle*Math.PI/180;return [radius*Math.cos(a),radius*Math.sin(a)];}
function spRegular(n,r,angle=0){return Array.from({length:n},(_,i)=>spPolar(r,angle+360*i/n));}
function spStar(n,outer,inner,angle=0){return Array.from({length:2*n},(_,i)=>spPolar(i%2?inner:outer,angle+i*180/n));}
function spMove(points,x,y){return points.map(([px,py])=>[px+x,py+y]);}
export function spTile(id,u){
 const faces=[];
 const add=(points,tone,kind)=>faces.push({points,tone,kind});
 if(id==='starcross'){
  const r=u/2,k=Math.SQRT1_2/Math.cos(Math.PI/8),a=(1-Math.SQRT1_2)*u/2;
  add(spStar(8,r,r*k),0,'piece');
  const quarter=[[0,-u/2],[a,-Math.SQRT1_2*u/2],[a,-a],[Math.SQRT1_2*u/2,-a]];
  let cross=[];
  for(let i=0;i<4;i++){const c=Math.cos(i*Math.PI/2),s=Math.sin(i*Math.PI/2);cross.push(...quarter.map(([x,y])=>[x*c-y*s,x*s+y*c]));}
  add(spMove(cross,u/2,u/2),1,'piece');
 } else if(id==='octagons'||id==='rosette8'){
  const R=u/(2*Math.cos(Math.PI/8)),d=u*(1-Math.SQRT1_2);
  if(id==='octagons')add(spRegular(8,R,22.5),1,'piece');
  else {
   const outer=.36*u,inner=.21*u;
   add(spStar(8,outer,inner),0,'piece');
   for(let i=0;i<8;i++){const a=i*45;add([spPolar(outer,a),spPolar(inner,a+22.5),spPolar(R,a+22.5),spPolar(R,a-22.5),spPolar(inner,a-22.5)],i%2?1:3,'piece');}
  }
  add(spMove(spRegular(4,d),u/2,u/2),2,'piece');
 } else if(id==='hexstar'||id==='lozenges'){
  const R=u/Math.sqrt(3),inner=R/Math.sqrt(3);
  if(id==='hexstar')add(spStar(6,R,inner),0,'piece');
  for(let i=0;i<6;i++){
   const a=i*60;
   if(id==='lozenges')add([[0,0],spPolar(inner,a-30),spPolar(R,a),spPolar(inner,a+30)],i%3,'piece');
   add([spPolar(R,a),spPolar(R,a+60),spPolar(inner,a+30)],id==='lozenges'?3:(i%2?1:2),'piece');
  }
 } else if(id==='rosette12'){
  const R=u/Math.sqrt(3),inner=spStar(12,.69*R,.44*R);
  const border=Array.from({length:24},(_,i)=>{const a=i*15,normal=30+60*Math.round((a-30)/60);return spPolar(R*Math.cos(Math.PI/6)/Math.cos((a-normal)*Math.PI/180),a);});
  add(inner,0,'piece');
  for(let i=0;i<24;i++){const j=(i+1)%24;add([inner[i],border[i],border[j],inner[j]],1+Math.floor(i/2)%3,'piece');}
 }
 return faces;
}
export function spMedallion(id,R){
 const faces=[],add=(points,tone,kind)=>faces.push({points,tone,kind});
 if(id==='medallion10'){
  const core=spStar(10,R*.32,R*.18,-90),ring=spStar(10,R*.73,R*.55,-90);
  const border=Array.from({length:20},(_,i)=>spPolar(i%2?R*Math.cos(Math.PI/10):R,-90+i*18));
  add(core,0,'piece');
  for(let i=0;i<20;i++){
   const j=(i+1)%20;
   add([core[i],core[j],ring[j],ring[i]],i%2?1:3,'piece');
   add([ring[i],ring[j],border[j],border[i]],i%2?2:0,'piece');
  }
 }else{
  const k=(3-Math.sqrt(5))/2;
  // Each level partitions a pentagon into the star's arms, its surrounding
  // triangles, and a smaller central pentagon. No faces overlap.
  for(let level=0;level<3;level++){
   const radius=R*Math.pow(k,level),angle=-90+level*36;
   const p=spStar(5,radius,radius*k,angle);
   for(let i=0;i<5;i++){
    add([p[2*i],p[(2*i+2)%10],p[2*i+1]],level%2?3:1,'piece');
    add([p[(2*i+9)%10],p[2*i],p[(2*i+1)%10]],level%2?2:0,'piece');
   }
   if(level===2)add(p.filter((_,i)=>i%2),3,'piece');
  }
 }
 return faces;
}
export function spScene(pattern,width,height,scale=100,angle=0,thumbnail=false){
 const all=[],u=Math.min(width,height)*(thumbnail?.52:.26)*scale/100;
 const a=angle*Math.PI/180,c=Math.cos(a),s=Math.sin(a);
 function add(local,key,x,y){
  for(let i=0;i<local.length;i++){
   const f=local[i],points=f.points.map(([px,py])=>{const dx=px+x,dy=py+y;return [width/2+dx*c-dy*s,height/2+dx*s+dy*c];});
   const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
   if(Math.max(...xs)<0||Math.min(...xs)>width||Math.max(...ys)<0||Math.min(...ys)>height)continue;
   const cx=xs.reduce((a,b)=>a+b,0)/xs.length,cy=ys.reduce((a,b)=>a+b,0)/ys.length;
   all.push({...f,points,key:`${pattern.id}-${key}-${i}`,cx,cy});
  }
 }
 if(pattern.grid==='radial')add(spMedallion(pattern.id,Math.min(width,height)*(thumbnail?.46:.35)*scale/100),'centre',0,0);
 else{
  const ex=Math.abs(c)*width/2+Math.abs(s)*height/2+u,ey=Math.abs(s)*width/2+Math.abs(c)*height/2+u;
  const faces=spTile(pattern.id,u),dx=pattern.grid==='hex'?u*Math.sqrt(3)/2:u;
  for(let col=-Math.ceil(ex/dx);col<=Math.ceil(ex/dx);col++)for(let row=-Math.ceil(ey/u)-1;row<=Math.ceil(ey/u)+1;row++){
   const y=row*u+(pattern.grid==='hex'&&Math.abs(col)%2?u/2:0);
   add(faces,`${col}_${row}`,col*dx,y);
  }
 }
 return all;
}
