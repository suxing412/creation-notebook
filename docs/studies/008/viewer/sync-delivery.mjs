/** Run only when delivery-links.js intentionally changes. Keeps no-JS HTML honest. */
import fs from 'node:fs';
import {deliveryFor} from './delivery-links.js';
const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const file=new URL('./index.html',import.meta.url),html=fs.readFileSync(file,'utf8');let count=0;
const updated=html.replace(/<a\b([^>]*\bdata-delivery-variant="([^"]+)"[^>]*\bdata-delivery-key="([^"]+)"[^>]*)>[^<]*<\/a>/g,(_,attrs,id,key)=>{const link=deliveryFor(id)[key];if(!link)throw Error('Unknown delivery key '+id+'/'+key);attrs=attrs.replace(/\s(?:href|download)="[^"]*"/g,'');count++;return `<a${attrs} href="${escape(link.href)}"${link.download?` download="${escape(link.download)}"`:''}>${escape(link.label)}</a>`;});
if(count!==16)throw Error('Expected 16 explicit delivery links, found '+count);fs.writeFileSync(file,updated);console.log('Synchronized 16 no-JS delivery links from delivery-links.js; no metadata edited.');
