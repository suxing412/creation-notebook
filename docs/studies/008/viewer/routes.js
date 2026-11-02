export const VARIANTS=Object.freeze({
 veil:{label:'Veil · 透幕',short:'透幕',text:'轻弧里的竖向节奏。孔洞贯穿陶瓷实体，明暗来自厚度，而不是透明贴图。'},
 horizon:{label:'Horizon · 横幕',short:'横幕',text:'更宽、更低，弧度收敛。横向铺开的孔列，让实体与空处在同一尺度下重新分配。'},
 fold:{label:'Fold · 曲幕',short:'曲幕',text:'更窄、更高，弧度加深。侧面与俯视揭示弯曲深度；屏体沿连续圆柱曲面弯曲，不包含折线。'}
});
export const VIEWS=Object.freeze({beauty:'主视',front:'正面',side:'侧面',top:'俯视',rear:'背面','hole-detail':'孔沿近景'});
export const DEFAULT_ROUTE=Object.freeze({id:'veil',view:'beauty'});
export function readRoute(input){const u=new URL(input,'https://local.invalid/');return {id:Object.hasOwn(VARIANTS,u.searchParams.get('variant'))?u.searchParams.get('variant'):'veil',view:Object.hasOwn(VIEWS,u.searchParams.get('view'))?u.searchParams.get('view'):'beauty'};}
export function routeURL(input,route){const u=new URL(input,'https://local.invalid/');u.searchParams.set('variant',route.id);u.searchParams.set('view',route.view);return u;}
export function sameRoute(a,b){return a.id===b.id&&a.view===b.view;}
export function cycleView(view,delta){const keys=Object.keys(VIEWS);return keys[(keys.indexOf(view)+delta+keys.length)%keys.length];}
