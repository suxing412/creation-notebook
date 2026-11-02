// Exact localPath function observed before the parent fixed whitespace.
// Original pose-state.js SHA256: 1d083bf24994a5b93a4529e154d7d35b2c12deafa5aedd64d43ddd2aaf7905d4.
function localPath(s){return typeof s==='string'&&s.length>0&&!/^[a-z][\w+.-]*:/i.test(s)&&!s.startsWith('/')&&!/[\\%?#\x00-\x1f]/.test(s)&&s.split('/').every(p=>p&&p!=='.'&&p!=='..');}
console.log([' ../outside.png','model/.. ',' javascript:alert(1)',' http:outside.invalid'].map(s=>({input:s,originalAccepted:localPath(s),url:new URL(s,'https://fixture.invalid/studies/009/index.html').href})));
