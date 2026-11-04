export function assembleFar44(THREE, roots, contract, manifest, {excludeIds=[]}={}) {
 const ids=new Set(manifest.rows.map(r=>r.id));if(ids.size!==44||manifest.rows.length!==44)throw Error('Expected 44 unique source IDs');
 const excluded=new Set(excludeIds);for(const id of excluded)if(!ids.has(id))throw Error('Unknown exclusion '+id);
 const group=new THREE.Group();group.name='real-courtyards-LOD1';const owned=[];const active=manifest.rows.filter(r=>!excluded.has(r.id));
 for(const r of active)if(r.scale.some(v=>v!==1)||r.matrixGLTFColumnMajor.length!==16||!r.matrixGLTFColumnMajor.every(Number.isFinite))throw Error('Invalid transform '+r.id);
 for(const a of contract.assets){const rows=active.filter(r=>r.variant===a.variant);if(!rows.length)continue;const root=roots.get(a.variant);if(!root)throw Error('Missing actual prototype '+a.variant);root.updateMatrixWorld(true);
 root.traverse(o=>{if(!o.isMesh||a.removable_site_nodes.includes(o.name))return;const geometry=o.geometry.clone().applyMatrix4(o.matrixWorld);const mesh=new THREE.InstancedMesh(geometry,o.material,rows.length);mesh.name=a.variant+':'+o.name;mesh.userData={lotIds:rows.map(r=>r.id),variant:a.variant,lod:1,sourceNode:o.name};rows.forEach((r,i)=>mesh.setMatrixAt(i,new THREE.Matrix4().fromArray(r.matrixGLTFColumnMajor)));mesh.instanceMatrix.needsUpdate=true;mesh.computeBoundingBox();mesh.computeBoundingSphere();group.add(mesh);owned.push(mesh);});}
 const represented=new Set(owned.flatMap(m=>m.userData.lotIds));if(represented.size!==active.length)throw Error('Unrepresented instance');
 return {group,activeIds:[...represented],excludedIds:[...excluded],dispose(){for(const m of owned){m.geometry.dispose();m.dispose();}group.clear();}};
}
