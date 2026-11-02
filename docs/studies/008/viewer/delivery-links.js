/** Delivery-only URLs and labels. Never change model metadata to describe packaging.
 * Source delivery is the raw .blend. For hosted compression, change only this map,
 * then run `node viewer/sync-delivery.mjs` to keep no-JS links and labels identical.
 */
export const DELIVERY_LINKS = Object.freeze(Object.fromEntries(['veil','horizon','fold'].map(id=>[id,Object.freeze({
 glb: {href:`../assets/${id}/model.glb`,label:'GLB 模型',download:`veil-008-${id}.glb`},
 blend: {href:`../assets/${id}/model.blend`,label:'Blender 原文件 · .blend',download:`veil-008-${id}.blend`},
 config: {href:`../assets/${id}/config.json`,label:'参数 JSON',download:''},
 info: {href:`../assets/${id}/model-info.json`,label:'模型记录',download:''}
})])));
export function deliveryFor(id){if(!Object.hasOwn(DELIVERY_LINKS,id))throw Error('Unknown delivery identity');return DELIVERY_LINKS[id];}
